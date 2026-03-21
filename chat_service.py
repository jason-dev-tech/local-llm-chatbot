from db import (
    save_message,
    get_recent_messages,
    get_all_sessions,
    create_session,
    update_session_title,
    session_exists,
    delete_session,
    get_session_messages,
)
from llm import stream_response, generate_session_title

SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."


# ===== Core Chat Logic =====

def build_messages(session_id):
    history = get_recent_messages(session_id, limit=10)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history


def send_message_and_stream(session_id, user_input):
    # Save user message
    save_message(session_id, "user", user_input)

    # Generate title for first message
    history = get_recent_messages(session_id, limit=1)
    if len(history) == 1:
        try:
            title = generate_session_title(user_input)
            update_session_title(session_id, title)
        except Exception:
            pass

    messages = build_messages(session_id)

    answer_parts = []

    for token in stream_response(messages):
        answer_parts.append(token)
        yield token

    answer = "".join(answer_parts)

    # Save assistant response
    save_message(session_id, "assistant", answer)


def send_message(session_id, user_input):
    """
    Non-stream version (for FastAPI later)
    """
    save_message(session_id, "user", user_input)

    history = get_recent_messages(session_id, limit=1)
    if len(history) == 1:
        try:
            title = generate_session_title(user_input)
            update_session_title(session_id, title)
        except Exception:
            pass

    messages = build_messages(session_id)

    from llm import generate_response
    answer = generate_response(messages)

    save_message(session_id, "assistant", answer)

    return answer


# ===== Session Management =====

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
    create_session(session_id)
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


# ===== Query (for Web API later) =====

def get_session_detail(session_id):
    if not session_exists(session_id):
        return None

    messages = get_session_messages(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
    }