import json
import logging
import os
import queue
import re
import time
import threading

from db import (
    save_message,
    get_recent_messages,
    get_all_sessions,
    create_session,
    update_session_title,
    session_exists,
    delete_session,
    get_session_messages,
    get_session_title,
)

from llm import generate_response
from llm_langchain import (
    generate_langchain_response,
    stream_langchain_chat_response,
)
from rag.langgraph_workflow import build_rag_workflow
from rag.retrieval import retrieve_relevant_chunks
from rag.router import get_routing_decision
from rag.source_metadata import resolve_chunk_source
from routing.llm_router import get_llm_routing_decision
from tools.registry import get_tool
from tools.router import get_tool_routing_decision, maybe_run_tool

SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."
INSUFFICIENT_EVIDENCE_RESPONSE = (
    "I couldn't find enough relevant evidence in the knowledge base to answer that confidently."
)
MIN_RELEVANT_RERANK_SCORE = 0.45
MIN_QUERY_TOKEN_OVERLAP = 2
MIN_SIGNIFICANT_TOKEN_LENGTH = 3
LOW_INFORMATION_QUERY_TOKENS = {
    "what",
    "when",
    "where",
    "which",
    "while",
    "this",
    "that",
    "with",
    "from",
    "into",
    "about",
    "have",
    "does",
    "would",
    "could",
    "should",
    "there",
    "their",
    "they",
    "them",
    "your",
    "data",
    "memory",
}
GENERIC_EVIDENCE_TOKENS = {
    "api",
    "architecture",
    "config",
    "design",
    "documentation",
    "endpoint",
    "implementation",
    "model",
    "policy",
    "protocol",
    "schema",
    "specification",
    "stand",
    "version",
    "workflow",
}
DEFINITION_QUERY_PATTERNS = (
    "what is ",
    "what are ",
    "what does ",
    "define ",
)
SESSION_TITLE_PROMPT = (
    "Generate a short and concise title for a chat session based on the user's first message. "
    "Return only the title, with no quotes or extra explanation. Keep it under 8 words.\n\n"
    "User message:\n{user_message}"
)
CITATION_PATTERN = re.compile(r"\[(\d+)\]")
NON_STANDARD_SOURCE_CITATION_PATTERN = re.compile(r"\[source\s+(\d+)\]", re.IGNORECASE)
ATTRIBUTION_BLOCK_PATTERN = re.compile(
    r"(?:^|\n\n)Sources:\n(?:(?:Sources used|Retrieved context):\n(?:- .*(?:\n|$))+)+",
    re.IGNORECASE,
)
ATTRIBUTION_SECTION_PATTERN = re.compile(
    r"(?:^|\n\n)(?:sources used|retrieved context):\n(?:- .*(?:\n|$))+",
    re.IGNORECASE,
)
WORD_PATTERN = re.compile(r"\b[a-z0-9]+\b")
COMPOUND_TERM_PATTERN = re.compile(r"\b[a-z0-9]+(?:[-_][a-z0-9]+)+\b")
FILENAME_LIKE_PATTERN = re.compile(r"\b[\w.-]+\.[A-Za-z0-9]+\b")
SUMMARIZE_TOOL_NAME = "summarize_text"
LOGGER = logging.getLogger("chatbot.observability")


def elapsed_ms(started_at):
    return round((time.perf_counter() - started_at) * 1000, 2)


def build_messages(session_id):
    history = get_recent_messages(session_id, limit=10)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history


def log_observability_event(stage, **fields):
    payload = {"stage": stage, **fields}
    LOGGER.info(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def get_retrieved_filenames(chunks):
    filenames = []
    for chunk in chunks:
        filename = chunk.get("metadata", {}).get("filename")
        if isinstance(filename, str) and filename.strip():
            filenames.append(filename.strip())
    return list(dict.fromkeys(filenames))


def get_used_source_labels(answer, chunks):
    cited_source_numbers = extract_cited_source_numbers(answer)
    if not cited_source_numbers:
        return []

    return [
        source["label"]
        for source in extract_source_list(chunks)
        if source["number"] in cited_source_numbers
    ]


def log_response_observability(
    session_id,
    user_query,
    route,
    tool_name,
    chunks,
    answer,
    started_at,
    response_mode,
    *,
    route_decision_latency_ms=None,
    retrieval_latency_ms=None,
    llm_generation_latency_ms=None,
):
    payload = {
        "session_id": session_id,
        "user_query": user_query,
        "effective_route": route,
        "response_mode": response_mode,
        "tool_used": tool_name,
        "retrieved_filenames": get_retrieved_filenames(chunks),
        "retrieved_chunk_count": len(chunks),
        "sources_used": get_used_source_labels(answer, chunks),
        "latency_ms": elapsed_ms(started_at),
    }

    if route_decision_latency_ms is not None:
        payload["route_decision_latency_ms"] = route_decision_latency_ms
    if retrieval_latency_ms is not None:
        payload["retrieval_latency_ms"] = retrieval_latency_ms
    if llm_generation_latency_ms is not None:
        payload["llm_generation_latency_ms"] = llm_generation_latency_ms

    log_observability_event("response", **payload)


def log_guardrail_observability(session_id, user_query, route, chunks, started_at):
    log_observability_event(
        "guardrail",
        session_id=session_id,
        user_query=user_query,
        effective_route=route,
        guardrail_type="insufficient_evidence",
        retrieved_filenames=get_retrieved_filenames(chunks),
        retrieved_chunk_count=len(chunks),
        latency_ms=elapsed_ms(started_at),
    )


def log_error_observability(session_id, user_query, route, tool_name, chunks, started_at, error):
    log_observability_event(
        "error",
        session_id=session_id,
        user_query=user_query,
        effective_route=route or "unknown",
        tool_used=tool_name,
        retrieved_filenames=get_retrieved_filenames(chunks),
        retrieved_chunk_count=len(chunks),
        error_type=type(error).__name__,
        latency_ms=elapsed_ms(started_at),
    )


def get_tool_name_for_query(user_input, tool_result):
    if isinstance(tool_result, str) and tool_result.startswith("{"):
        return "extract_entities"

    decision = get_tool_routing_decision(user_input)
    return decision.tool_name


def get_response_mode(route, tool_name, *, evidence_sufficient=None):
    if route == "tool" or tool_name:
        return "tool"
    if route == "rag":
        if evidence_sufficient is False:
            return "insufficient_evidence"
        return "rag_response"
    return "chat"


def build_source_map(chunks):
    source_map = {}

    for chunk in chunks:
        source = resolve_chunk_source(chunk)
        if source not in source_map:
            source_map[source] = len(source_map) + 1

    return source_map


def has_usable_retrieval_evidence(user_input, chunks):
    normalized_query = user_input.strip().lower()
    query_tokens = tokenize_text(user_input)
    meaningful_query_tokens = {
        token for token in query_tokens
        if (
            len(token) >= MIN_SIGNIFICANT_TOKEN_LENGTH
            and token not in LOW_INFORMATION_QUERY_TOKENS
            and token not in GENERIC_EVIDENCE_TOKENS
        )
    }
    is_definition_query = normalized_query.startswith(DEFINITION_QUERY_PATTERNS)
    compound_query_terms = {
        match.group(0)
        for match in COMPOUND_TERM_PATTERN.finditer(normalized_query)
    }

    for chunk in chunks:
        content = chunk.get("content", "")
        if not isinstance(content, str) or not content.strip():
            continue

        normalized_content = content.lower()
        chunk_tokens = tokenize_text(content)
        rerank_score = chunk.get("rerank_score")
        overlap_count = len(meaningful_query_tokens & chunk_tokens) if meaningful_query_tokens else 0

        if is_definition_query:
            required_overlap = 2 if len(meaningful_query_tokens) > 1 else 1
            overlap_ok = overlap_count >= required_overlap
            if compound_query_terms:
                overlap_ok = overlap_ok and any(
                    compound_term in normalized_content
                    for compound_term in compound_query_terms
                )
        else:
            overlap_ok = overlap_count >= MIN_QUERY_TOKEN_OVERLAP

        rerank_ok = (
            isinstance(rerank_score, (int, float))
            and rerank_score >= MIN_RELEVANT_RERANK_SCORE
        )

        if overlap_ok and rerank_ok:
            return True

    return False


def format_source_label(source, metadata):
    source_type = metadata.get("source_type")
    if isinstance(source_type, str) and source_type.startswith("json_"):
        filename = metadata.get("filename")
        record_title = metadata.get("record_title") or metadata.get("title")

        if isinstance(filename, str) and filename.strip():
            base_label = filename.strip()
        elif isinstance(source, str) and source.strip():
            normalized_source = source.strip()
            file_name = os.path.basename(normalized_source)
            base_label = file_name or normalized_source
        else:
            base_label = "Unknown"

        if isinstance(record_title, str) and record_title.strip():
            return f"{base_label} ({record_title.strip()})"

        return base_label

    preferred_label = (
        metadata.get("title")
        or metadata.get("name")
        or metadata.get("label")
    )
    if isinstance(preferred_label, str) and preferred_label.strip():
        return preferred_label.strip()

    if not isinstance(source, str) or not source.strip():
        return "Unknown"

    normalized_source = source.strip()
    file_name = os.path.basename(normalized_source)

    if file_name and file_name != normalized_source:
        return file_name

    if "/" in normalized_source or "\\" in normalized_source:
        return file_name or normalized_source

    return normalized_source.replace("_", " ").replace("-", " ").title()


def build_citation_context_text(chunks):
    if not chunks:
        return ""

    source_map = build_source_map(chunks)
    context_parts = []

    for chunk in chunks:
        source = resolve_chunk_source(chunk)
        source_number = source_map[source]
        content = chunk["content"]
        context_parts.append(f"[Source {source_number}] {source}\n{content}")

    return "\n\n".join(context_parts)


def tokenize_text(text):
    return set(WORD_PATTERN.findall(text.lower()))


def choose_citation_number(text, chunks, source_map):
    text_tokens = tokenize_text(text)
    if not text_tokens:
        return None

    best_number = None
    best_score = 0

    for chunk in chunks:
        source = resolve_chunk_source(chunk)
        source_number = source_map[source]
        chunk_tokens = tokenize_text(chunk.get("content", ""))
        score = len(text_tokens & chunk_tokens)

        if score > best_score or (score == best_score and score > 0 and source_number < best_number):
            best_score = score
            best_number = source_number

    if best_score > 0:
        return best_number

    if len(source_map) == 1:
        return next(iter(source_map.values()))

    return None


def append_citation_marker(text, citation_number):
    stripped = text.rstrip()
    trailing = text[len(stripped):]
    return f"{stripped} [{citation_number}]{trailing}"


def normalize_answer_body(answer):
    normalized = NON_STANDARD_SOURCE_CITATION_PATTERN.sub(r"[\1]", answer)
    normalized = ATTRIBUTION_BLOCK_PATTERN.sub("", normalized)
    normalized = ATTRIBUTION_SECTION_PATTERN.sub("", normalized)
    return normalized.strip()


def apply_inline_citations(answer, chunks):
    if not chunks:
        return answer

    source_map = build_source_map(chunks)
    paragraphs = answer.split("\n\n")
    use_sentence_fallback = len([paragraph for paragraph in paragraphs if paragraph.strip()]) <= 1

    if use_sentence_fallback:
        blocks = re.split(r"(?<=[.!?])\s+", answer)
        separator = " "
    else:
        blocks = paragraphs
        separator = "\n\n"

    updated_blocks = []
    has_any_citation = False

    for block in blocks:
        if not block.strip():
            updated_blocks.append(block)
            continue

        if CITATION_PATTERN.search(block):
            has_any_citation = True
            updated_blocks.append(block)
            continue

        citation_number = choose_citation_number(block, chunks, source_map)
        if citation_number is not None:
            block = append_citation_marker(block, citation_number)
            has_any_citation = True

        updated_blocks.append(block)

    if not has_any_citation and updated_blocks:
        fallback_number = next(iter(source_map.values()))

        for index in range(len(updated_blocks) - 1, -1, -1):
            if updated_blocks[index].strip():
                updated_blocks[index] = append_citation_marker(updated_blocks[index], fallback_number)
                break

    return separator.join(updated_blocks)


def build_rag_messages(session_id, user_input):
    history = get_recent_messages(session_id, limit=10)
    decision = get_effective_routing_decision(user_input)

    if decision.route != "rag":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        return messages, [], decision

    chunks = retrieve_relevant_chunks(
        user_input,
        top_k=3,
        file_filters=extract_retrieval_file_filters(user_input),
    )
    context_text = build_citation_context_text(chunks)

    if context_text:
        system_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "You are answering with the help of retrieved knowledge base context.\n"
            "Use the context below as the primary source when it is relevant to the user's question.\n"
            "If the context contains the answer, base your response on it.\n"
            "If the context is only partially relevant, use it carefully and make that clear.\n"
            "If the context does not contain enough information, say so clearly instead of making up facts.\n"
            "When you use information from the context, add inline citations using the source numbers, such as [1] or [2].\n"
            "Reuse the same citation number whenever the same source is used again.\n"
            "Do not add citations when you are not relying on the provided context.\n"
            "Keep the answer clear, concise, and grounded in the provided context when possible.\n\n"
            f"Context:\n{context_text}"
        )
    else:
        system_prompt = SYSTEM_PROMPT

    messages = [{"role": "system", "content": system_prompt}] + history
    return messages, chunks, decision


def build_grounded_rag_system_prompt(context_text, user_input):
    if not context_text:
        return SYSTEM_PROMPT

    return (
        f"{SYSTEM_PROMPT}\n\n"
        "You are answering with the help of retrieved knowledge base context.\n"
        "Use the context below as the primary source when it is relevant to the user's question.\n"
        "If the context contains the answer, base your response on it.\n"
        "If the context is only partially relevant, use it carefully and make that clear.\n"
        "If the context does not contain enough information, say so clearly instead of making up facts.\n"
        "When you use information from the context, add inline citations using the source numbers, such as [1] or [2].\n"
        "Reuse the same citation number whenever the same source is used again.\n"
        "Do not add citations when you are not relying on the provided context.\n"
        "Keep the answer clear, concise, and grounded in the provided context when possible.\n\n"
        f"Context:\n{context_text}"
    )


def format_rag_answer(answer, chunks):
    answer = normalize_answer_body(answer)
    answer = apply_inline_citations(answer, chunks)
    return append_sources_to_answer(answer, chunks)


def generate_rag_answer_stream(system_prompt, user_input, stream_callback=None):
    answer_parts = []
    for token in stream_langchain_chat_response(system_prompt, user_input):
        answer_parts.append(token)
        if stream_callback is not None:
            stream_callback(token)
    return "".join(answer_parts)


def ensure_current_user_message(history, user_input):
    if history and history[-1].get("role") == "user" and history[-1].get("content") == user_input:
        return history
    return history + [{"role": "user", "content": user_input}]


def invoke_rag_workflow_stream(initial_state):
    token_queue = queue.Queue()
    result = {}
    error_holder = {}

    def stream_callback(token):
        token_queue.put(token)

    def run_workflow():
        try:
            state = dict(initial_state)
            state["stream_callback"] = stream_callback
            result["state"] = RAG_WORKFLOW.invoke(state)
        except Exception as error:
            error_holder["error"] = error
        finally:
            token_queue.put(None)

    worker = threading.Thread(target=run_workflow, daemon=True)
    worker.start()

    while True:
        token = token_queue.get()
        if token is None:
            break
        yield token

    worker.join()

    if "error" in error_holder:
        raise error_holder["error"]

    return result.get("state", {})


RAG_WORKFLOW = build_rag_workflow(
    retrieve_chunks=retrieve_relevant_chunks,
    build_context_text=build_citation_context_text,
    build_system_prompt=build_grounded_rag_system_prompt,
    check_evidence=has_usable_retrieval_evidence,
    generate_sync=generate_response,
    generate_stream=generate_rag_answer_stream,
    format_answer=format_rag_answer,
    insufficient_response=INSUFFICIENT_EVIDENCE_RESPONSE,
)


def get_effective_routing_decision(user_input):
    heuristic_decision = get_routing_decision(user_input)
    if heuristic_decision.route == "rag":
        return heuristic_decision

    llm_decision = get_llm_routing_decision(user_input)
    if llm_decision.route == "rag":
        return llm_decision

    return heuristic_decision


def maybe_run_retrieval_summary(user_input):
    normalized = user_input.strip().lower()
    if not normalized.startswith("summarize") and not normalized.startswith("summary"):
        return None

    explicit_text_markers = (
        "this text:",
        "the following text:",
        "text:",
    )
    if any(marker in normalized for marker in explicit_text_markers):
        return None

    decision = get_routing_decision(user_input)
    if decision.route != "rag":
        return None

    chunks = retrieve_relevant_chunks(
        user_input,
        top_k=3,
        file_filters=extract_retrieval_file_filters(user_input),
    )
    if not chunks:
        return "I couldn't find relevant knowledge to summarize."

    retrieved_text = "\n\n".join(
        chunk.get("content", "").strip()
        for chunk in chunks
        if chunk.get("content", "").strip()
    )
    if not retrieved_text:
        return "I couldn't find relevant knowledge to summarize."

    summary_prompt = (
        "Summarize the retrieved knowledge base content for the user's request.\n"
        "Requirements:\n"
        "- Keep the summary concise and natural.\n"
        "- Preserve the original meaning.\n"
        "- Stay strictly grounded in the retrieved content.\n"
        "- Do not generalize beyond what is explicitly supported.\n"
        "- Do not copy raw Q&A blocks or document structure.\n"
        "- Do not add new facts.\n"
        "- Return only the summary.\n\n"
        f"User request:\n{user_input}\n\n"
        f"Retrieved content:\n{retrieved_text}"
    )

    try:
        summary = generate_langchain_response(summary_prompt).strip()
    except Exception:
        summary = ""

    if not summary:
        return "I couldn't produce a summary from the retrieved knowledge."

    return append_sources_to_answer(summary, chunks)


def maybe_run_llm_routed_tool(user_input):
    llm_decision = get_llm_routing_decision(user_input)
    if llm_decision.route != f"tool:{SUMMARIZE_TOOL_NAME}":
        return None

    summarize_tool = get_tool(SUMMARIZE_TOOL_NAME)
    if summarize_tool is None:
        return None

    if not llm_decision.tool_input:
        return "Please provide text to summarize."

    return summarize_tool.run(llm_decision.tool_input)


def extract_retrieval_file_filters(user_input):
    if not FILENAME_LIKE_PATTERN.search(user_input):
        return None

    extract_entities_tool = get_tool("extract_entities")
    if extract_entities_tool is None:
        return None

    try:
        payload = json.loads(extract_entities_tool.run(user_input))
    except (TypeError, json.JSONDecodeError):
        return None

    files = payload.get("files", [])
    if not isinstance(files, list):
        return None

    normalized_files = [value.strip() for value in files if isinstance(value, str) and value.strip()]
    return normalized_files or None


def extract_source_list(chunks):
    source_map = build_source_map(chunks)
    source_metadata_map = {}

    for chunk in chunks:
        source = resolve_chunk_source(chunk)
        if source not in source_metadata_map:
            source_metadata_map[source] = chunk.get("metadata", {})

    return [
        {
            "source": source,
            "number": number,
            "label": format_source_label(source, source_metadata_map.get(source, {})),
        }
        for source, number in sorted(source_map.items(), key=lambda item: item[1])
    ]


def extract_cited_source_numbers(answer):
    return {int(match.group(1)) for match in CITATION_PATTERN.finditer(answer)}


def append_sources_to_answer(answer, chunks):
    sources = extract_source_list(chunks)

    if not sources:
        return answer

    cited_source_numbers = extract_cited_source_numbers(answer)
    used_sources = [source for source in sources if source["number"] in cited_source_numbers]
    retrieved_context_sources = [
        source for source in sources if source["number"] not in cited_source_numbers
    ]

    sections = []

    if used_sources:
        used_source_lines = [f"- [{source['number']}] {source['label']}" for source in used_sources]
        sections.append(f"Sources used:\n" + "\n".join(used_source_lines))

    if retrieved_context_sources:
        retrieved_context_lines = [
            f"- [{source['number']}] {source['label']}" for source in retrieved_context_sources
        ]
        sections.append(f"Retrieved context:\n" + "\n".join(retrieved_context_lines))

    if not sections:
        return answer

    return f"{answer}\n\nSources:\n" + "\n\n".join(sections)


def maybe_update_session_title(session_id, user_input):
    """
    Generate a session title only for a new/default session.
    """
    current_title = get_session_title(session_id)

    if current_title and current_title != "New Chat":
        return

    history = get_recent_messages(session_id, limit=1)
    if len(history) != 1:
        return

    try:
        title_prompt = SESSION_TITLE_PROMPT.format(user_message=user_input)
        title = generate_langchain_response(title_prompt).strip()

        if not title:
            return

        update_session_title(session_id, title[:60])
    except Exception:
        pass


def send_message_and_stream(session_id, user_input):
    started_at = time.perf_counter()
    route = None
    tool_name = None
    chunks = []
    route_decision_latency_ms = None
    retrieval_latency_ms = None
    llm_generation_latency_ms = None

    try:
        save_message(session_id, "user", user_input)

        maybe_update_session_title(session_id, user_input)

        tool_result = maybe_run_tool(user_input)
        if tool_result is not None:
            route = "tool"
            tool_name = get_tool_name_for_query(user_input, tool_result)
            log_observability_event(
                "route",
                session_id=session_id,
                user_query=user_input,
                effective_route=route,
                tool_used=tool_name,
            )
            save_message(session_id, "assistant", tool_result)
            log_response_observability(
                session_id,
                user_input,
                route,
                tool_name,
                chunks,
                tool_result,
                started_at,
                "tool",
            )
            yield tool_result
            return

        retrieval_summary_result = maybe_run_retrieval_summary(user_input)
        if retrieval_summary_result is not None:
            route = "rag"
            retrieval_started_at = time.perf_counter()
            chunks = retrieve_relevant_chunks(
                user_input,
                top_k=3,
                file_filters=extract_retrieval_file_filters(user_input),
            )
            retrieval_latency_ms = elapsed_ms(retrieval_started_at)
            log_observability_event(
                "route",
                session_id=session_id,
                user_query=user_input,
                effective_route=route,
                tool_used=None,
            )
            log_observability_event(
                "retrieval",
                session_id=session_id,
                user_query=user_input,
                effective_route=route,
                retrieved_filenames=get_retrieved_filenames(chunks),
                retrieved_chunk_count=len(chunks),
                retrieval_latency_ms=retrieval_latency_ms,
            )
            save_message(session_id, "assistant", retrieval_summary_result)
            log_response_observability(
                session_id,
                user_input,
                route,
                None,
                chunks,
                retrieval_summary_result,
                started_at,
                get_response_mode(
                    route,
                    None,
                    evidence_sufficient=has_usable_retrieval_evidence(user_input, chunks),
                ),
                retrieval_latency_ms=retrieval_latency_ms,
            )
            yield retrieval_summary_result
            return

        llm_tool_result = maybe_run_llm_routed_tool(user_input)
        if llm_tool_result is not None:
            route = "tool"
            tool_name = SUMMARIZE_TOOL_NAME
            log_observability_event(
                "route",
                session_id=session_id,
                user_query=user_input,
                effective_route=route,
                tool_used=tool_name,
            )
            save_message(session_id, "assistant", llm_tool_result)
            log_response_observability(
                session_id,
                user_input,
                route,
                tool_name,
                chunks,
                llm_tool_result,
                started_at,
                get_response_mode(route, tool_name, evidence_sufficient=None),
            )
            yield llm_tool_result
            return

        history = get_recent_messages(session_id, limit=10)
        route_started_at = time.perf_counter()
        decision = get_effective_routing_decision(user_input)
        route_decision_latency_ms = elapsed_ms(route_started_at)
        route = decision.route
        log_observability_event(
            "route",
            session_id=session_id,
            user_query=user_input,
            effective_route=route,
            tool_used=None,
            route_reason=decision.reason,
            route_confidence=decision.confidence,
            route_decision_latency_ms=route_decision_latency_ms,
        )
        if route != "rag":
            chunks = []
            generation_started_at = time.perf_counter()
            stream = stream_langchain_chat_response(SYSTEM_PROMPT, user_input)
            answer_parts = []

            for token in stream:
                answer_parts.append(token)
                yield token

            llm_generation_latency_ms = elapsed_ms(generation_started_at)
            answer = "".join(answer_parts)
            answer = normalize_answer_body(answer)
            save_message(session_id, "assistant", answer)
            log_response_observability(
                session_id,
                user_input,
                route,
                None,
                chunks,
                answer,
                started_at,
                get_response_mode(route, None, evidence_sufficient=None),
                route_decision_latency_ms=route_decision_latency_ms,
                llm_generation_latency_ms=llm_generation_latency_ms,
            )
            return

        workflow_state = yield from invoke_rag_workflow_stream(
            {
                "user_input": user_input,
                "history": history,
                "file_filters": extract_retrieval_file_filters(user_input),
                "mode": "stream",
            }
        )
        chunks = workflow_state.get("chunks", [])
        retrieval_latency_ms = workflow_state.get("retrieval_latency_ms")
        llm_generation_latency_ms = workflow_state.get("llm_generation_latency_ms")
        log_observability_event(
            "retrieval",
            session_id=session_id,
            user_query=user_input,
            effective_route=route,
            retrieved_filenames=get_retrieved_filenames(chunks),
            retrieved_chunk_count=len(chunks),
            retrieval_latency_ms=retrieval_latency_ms,
        )
        if not workflow_state.get("evidence_sufficient"):
            log_guardrail_observability(session_id, user_input, route, chunks, started_at)
            answer = workflow_state.get("final_answer", INSUFFICIENT_EVIDENCE_RESPONSE)
            save_message(session_id, "assistant", answer)
            log_response_observability(
                session_id,
                user_input,
                route,
                None,
                chunks,
                answer,
                started_at,
                get_response_mode(route, None, evidence_sufficient=False),
                route_decision_latency_ms=route_decision_latency_ms,
                retrieval_latency_ms=retrieval_latency_ms,
                llm_generation_latency_ms=llm_generation_latency_ms,
            )
            yield answer
            return

        answer = workflow_state.get("final_answer", "")
        save_message(session_id, "assistant", answer)
        log_response_observability(
            session_id,
            user_input,
            route,
            None,
            chunks,
            answer,
            started_at,
            get_response_mode(
                route,
                None,
                evidence_sufficient=True,
            ),
            route_decision_latency_ms=route_decision_latency_ms,
            retrieval_latency_ms=retrieval_latency_ms,
            llm_generation_latency_ms=llm_generation_latency_ms,
        )
    except Exception as error:
        log_error_observability(session_id, user_input, route, tool_name, chunks, started_at, error)
        raise


def send_message(session_id, user_input):
    started_at = time.perf_counter()
    route = None
    tool_name = None
    chunks = []
    route_decision_latency_ms = None
    retrieval_latency_ms = None
    llm_generation_latency_ms = None

    try:
        save_message(session_id, "user", user_input)

        maybe_update_session_title(session_id, user_input)

        tool_result = maybe_run_tool(user_input)
        if tool_result is not None:
            route = "tool"
            tool_name = get_tool_name_for_query(user_input, tool_result)
            log_observability_event(
                "route",
                session_id=session_id,
                user_query=user_input,
                effective_route=route,
                tool_used=tool_name,
            )
            save_message(session_id, "assistant", tool_result)
            log_response_observability(
                session_id,
                user_input,
                route,
                tool_name,
                chunks,
                tool_result,
                started_at,
                "tool",
            )
            return tool_result

        retrieval_summary_result = maybe_run_retrieval_summary(user_input)
        if retrieval_summary_result is not None:
            route = "rag"
            retrieval_started_at = time.perf_counter()
            chunks = retrieve_relevant_chunks(
                user_input,
                top_k=3,
                file_filters=extract_retrieval_file_filters(user_input),
            )
            retrieval_latency_ms = elapsed_ms(retrieval_started_at)
            log_observability_event(
                "route",
                session_id=session_id,
                user_query=user_input,
                effective_route=route,
                tool_used=None,
            )
            log_observability_event(
                "retrieval",
                session_id=session_id,
                user_query=user_input,
                effective_route=route,
                retrieved_filenames=get_retrieved_filenames(chunks),
                retrieved_chunk_count=len(chunks),
                retrieval_latency_ms=retrieval_latency_ms,
            )
            save_message(session_id, "assistant", retrieval_summary_result)
            log_response_observability(
                session_id,
                user_input,
                route,
                None,
                chunks,
                retrieval_summary_result,
                started_at,
                get_response_mode(
                    route,
                    None,
                    evidence_sufficient=has_usable_retrieval_evidence(user_input, chunks),
                ),
                retrieval_latency_ms=retrieval_latency_ms,
            )
            return retrieval_summary_result

        llm_tool_result = maybe_run_llm_routed_tool(user_input)
        if llm_tool_result is not None:
            route = "tool"
            tool_name = SUMMARIZE_TOOL_NAME
            log_observability_event(
                "route",
                session_id=session_id,
                user_query=user_input,
                effective_route=route,
                tool_used=tool_name,
            )
            save_message(session_id, "assistant", llm_tool_result)
            log_response_observability(
                session_id,
                user_input,
                route,
                tool_name,
                chunks,
                llm_tool_result,
                started_at,
                get_response_mode(route, tool_name, evidence_sufficient=None),
            )
            return llm_tool_result

        history = get_recent_messages(session_id, limit=10)
        route_started_at = time.perf_counter()
        decision = get_effective_routing_decision(user_input)
        route_decision_latency_ms = elapsed_ms(route_started_at)
        route = decision.route
        log_observability_event(
            "route",
            session_id=session_id,
            user_query=user_input,
            effective_route=route,
            tool_used=None,
            route_reason=decision.reason,
            route_confidence=decision.confidence,
            route_decision_latency_ms=route_decision_latency_ms,
        )
        if route != "rag":
            chunks = []
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + ensure_current_user_message(history, user_input)
            generation_started_at = time.perf_counter()
            answer = generate_response(messages)
            llm_generation_latency_ms = elapsed_ms(generation_started_at)
            answer = normalize_answer_body(answer)
            save_message(session_id, "assistant", answer)
            log_response_observability(
                session_id,
                user_input,
                route,
                None,
                chunks,
                answer,
                started_at,
                get_response_mode(route, None, evidence_sufficient=None),
                route_decision_latency_ms=route_decision_latency_ms,
                llm_generation_latency_ms=llm_generation_latency_ms,
            )
            return answer

        workflow_state = RAG_WORKFLOW.invoke(
            {
                "user_input": user_input,
                "history": history,
                "file_filters": extract_retrieval_file_filters(user_input),
                "mode": "sync",
            }
        )
        chunks = workflow_state.get("chunks", [])
        retrieval_latency_ms = workflow_state.get("retrieval_latency_ms")
        llm_generation_latency_ms = workflow_state.get("llm_generation_latency_ms")
        log_observability_event(
            "retrieval",
            session_id=session_id,
            user_query=user_input,
            effective_route=route,
            retrieved_filenames=get_retrieved_filenames(chunks),
            retrieved_chunk_count=len(chunks),
            retrieval_latency_ms=retrieval_latency_ms,
        )
        if not workflow_state.get("evidence_sufficient"):
            log_guardrail_observability(session_id, user_input, route, chunks, started_at)
            answer = workflow_state.get("final_answer", INSUFFICIENT_EVIDENCE_RESPONSE)
            save_message(session_id, "assistant", answer)
            log_response_observability(
                session_id,
                user_input,
                route,
                None,
                chunks,
                answer,
                started_at,
                get_response_mode(route, None, evidence_sufficient=False),
                route_decision_latency_ms=route_decision_latency_ms,
                retrieval_latency_ms=retrieval_latency_ms,
                llm_generation_latency_ms=llm_generation_latency_ms,
            )
            return answer

        answer = workflow_state.get("final_answer", "")

        save_message(session_id, "assistant", answer)
        log_response_observability(
            session_id,
            user_input,
            route,
            None,
            chunks,
            answer,
            started_at,
            get_response_mode(
                route,
                None,
                evidence_sufficient=True,
            ),
            route_decision_latency_ms=route_decision_latency_ms,
            retrieval_latency_ms=retrieval_latency_ms,
            llm_generation_latency_ms=llm_generation_latency_ms,
        )
        return answer
    except Exception as error:
        log_error_observability(session_id, user_input, route, tool_name, chunks, started_at, error)
        raise


def generate_new_session_id():
    sessions = get_all_sessions()

    if not sessions:
        return "session_1"

    numbers = []
    for session in sessions:
        if session.startswith("session_"):
            suffix = session.replace("session_", "")
            if suffix.isdigit():
                numbers.append(int(suffix))

    return f"session_{max(numbers) + 1}" if numbers else "session_1"


def get_initial_session():
    sessions = get_all_sessions()
    return sessions[-1] if sessions else "session_1"


def create_new_session():
    session_id = generate_new_session_id()
    create_session(session_id, "New Chat")
    return session_id


def switch_session(target_session):
    if not session_exists(target_session):
        return None
    return target_session


def rename_session(session_id, new_title):
    update_session_title(session_id, new_title)


def remove_session(target_session):
    if not session_exists(target_session):
        return False

    delete_session(target_session)
    return True


def get_session_detail(session_id):
    if not session_exists(session_id):
        return None

    messages = get_session_messages(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
    }
