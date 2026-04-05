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
from rag.retrieval import retrieve_relevant_chunks, build_context_text
from rag.router import should_use_rag

SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."
SESSION_TITLE_PROMPT = (
    "Generate a short and concise title for a chat session based on the user's first message. "
    "Return only the title, with no quotes or extra explanation. Keep it under 8 words.\n\n"
    "User message:\n{user_message}"
)


def build_messages(session_id):
    history = get_recent_messages(session_id, limit=10)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history


def build_rag_messages(session_id, user_input):
    history = get_recent_messages(session_id, limit=10)

    if not should_use_rag(user_input):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        return messages, []

    chunks = retrieve_relevant_chunks(user_input, top_k=3)
    context_text = build_context_text(chunks)

    if context_text:
        system_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "You are answering with the help of retrieved knowledge base context.\n"
            "Use the context below as the primary source when it is relevant to the user's question.\n"
            "If the context contains the answer, base your response on it.\n"
            "If the context is only partially relevant, use it carefully and make that clear.\n"
            "If the context does not contain enough information, say so clearly instead of making up facts.\n"
            "Keep the answer clear, concise, and grounded in the provided context when possible.\n\n"
            f"Context:\n{context_text}"
        )
    else:
        system_prompt = SYSTEM_PROMPT

    messages = [{"role": "system", "content": system_prompt}] + history
    return messages, chunks


def extract_source_list(chunks):
    seen = set()
    sources = []

    for chunk in chunks:
        source = chunk.get("metadata", {}).get("source")
        if not source or source in seen:
            continue

        seen.add(source)
        sources.append(source)

    return sources


def append_sources_to_answer(answer, chunks):
    sources = extract_source_list(chunks)

    if not sources:
        return answer

    source_lines = [f"- {source}" for source in sources]
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
    answer = append_sources_to_answer(answer, chunks)
    save_message(session_id, "assistant", answer)


def send_message(session_id, user_input):
    save_message(session_id, "user", user_input)

    maybe_update_session_title(session_id, user_input)

    messages, chunks = build_rag_messages(session_id, user_input)
    answer = generate_response(messages)
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
