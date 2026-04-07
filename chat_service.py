import json
import os
import re

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
from rag.retrieval import retrieve_relevant_chunks
from rag.router import get_routing_decision
from rag.source_metadata import resolve_chunk_source
from routing.llm_router import get_llm_routing_decision
from tools.registry import get_tool
from tools.router import maybe_run_tool

SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."
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
FILENAME_LIKE_PATTERN = re.compile(r"\b[\w.-]+\.[A-Za-z0-9]+\b")
SUMMARIZE_TOOL_NAME = "summarize_text"


def build_messages(session_id):
    history = get_recent_messages(session_id, limit=10)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history


def build_source_map(chunks):
    source_map = {}

    for chunk in chunks:
        source = resolve_chunk_source(chunk)
        if source not in source_map:
            source_map[source] = len(source_map) + 1

    return source_map


def format_source_label(source, metadata):
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
    print(
        f"Routing decision: route={decision.route} "
        f"reason={decision.reason} confidence={decision.confidence}"
    )

    if decision.route != "rag":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        return messages, []

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
    return messages, chunks


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
    save_message(session_id, "user", user_input)

    maybe_update_session_title(session_id, user_input)

    tool_result = maybe_run_tool(user_input)
    if tool_result is not None:
        save_message(session_id, "assistant", tool_result)
        yield tool_result
        return

    retrieval_summary_result = maybe_run_retrieval_summary(user_input)
    if retrieval_summary_result is not None:
        save_message(session_id, "assistant", retrieval_summary_result)
        yield retrieval_summary_result
        return

    llm_tool_result = maybe_run_llm_routed_tool(user_input)
    if llm_tool_result is not None:
        save_message(session_id, "assistant", llm_tool_result)
        yield llm_tool_result
        return

    messages, chunks = build_rag_messages(session_id, user_input)
    answer_parts = []

    if chunks:
        stream = stream_langchain_chat_response(messages[0]["content"], user_input)
    else:
        stream = stream_langchain_chat_response(SYSTEM_PROMPT, user_input)

    for token in stream:
        answer_parts.append(token)
        yield token

    answer = "".join(answer_parts)
    answer = normalize_answer_body(answer)
    answer = apply_inline_citations(answer, chunks)
    answer = append_sources_to_answer(answer, chunks)
    save_message(session_id, "assistant", answer)


def send_message(session_id, user_input):
    save_message(session_id, "user", user_input)

    maybe_update_session_title(session_id, user_input)

    tool_result = maybe_run_tool(user_input)
    if tool_result is not None:
        save_message(session_id, "assistant", tool_result)
        return tool_result

    retrieval_summary_result = maybe_run_retrieval_summary(user_input)
    if retrieval_summary_result is not None:
        save_message(session_id, "assistant", retrieval_summary_result)
        return retrieval_summary_result

    llm_tool_result = maybe_run_llm_routed_tool(user_input)
    if llm_tool_result is not None:
        save_message(session_id, "assistant", llm_tool_result)
        return llm_tool_result

    messages, chunks = build_rag_messages(session_id, user_input)
    answer = generate_response(messages)
    answer = normalize_answer_body(answer)
    answer = apply_inline_citations(answer, chunks)
    answer = append_sources_to_answer(answer, chunks)

    save_message(session_id, "assistant", answer)
    return answer


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
