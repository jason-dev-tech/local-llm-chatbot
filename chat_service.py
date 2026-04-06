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

SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."
SESSION_TITLE_PROMPT = (
    "Generate a short and concise title for a chat session based on the user's first message. "
    "Return only the title, with no quotes or extra explanation. Keep it under 8 words.\n\n"
    "User message:\n{user_message}"
)
CITATION_PATTERN = re.compile(r"\[(\d+)\]")
WORD_PATTERN = re.compile(r"\b[a-z0-9]+\b")


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
    decision = get_routing_decision(user_input)
    print(
        f"Routing decision: route={decision.route} "
        f"reason={decision.reason} confidence={decision.confidence}"
    )

    if decision.route != "rag":
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        return messages, []

    chunks = retrieve_relevant_chunks(user_input, top_k=3)
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


def append_sources_to_answer(answer, chunks):
    sources = extract_source_list(chunks)

    if not sources:
        return answer

    source_lines = [f"- [{source['number']}] {source['label']}" for source in sources]
    source_text = "\n".join(source_lines)

    return f"{answer}\n\nSources:\n{source_text}"


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
    answer = apply_inline_citations(answer, chunks)
    answer = append_sources_to_answer(answer, chunks)
    save_message(session_id, "assistant", answer)


def send_message(session_id, user_input):
    save_message(session_id, "user", user_input)

    maybe_update_session_title(session_id, user_input)

    messages, chunks = build_rag_messages(session_id, user_input)
    answer = generate_response(messages)
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
