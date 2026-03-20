from openai import OpenAI
from config import MODEL_NAME, BASE_URL, API_KEY
from db import (
    init_db,
    save_message,
    get_recent_messages,
    get_all_sessions,
    create_session,
    update_session_title,
    get_all_sessions_with_titles,
    session_exists,
    delete_session,
)

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."


def build_messages(session_id):
    history = get_recent_messages(session_id, limit=10)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history


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


def generate_session_title(user_input):
    prompt = [
        {
            "role": "system",
            "content": "Generate a short title of at most 5 words for this conversation."
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=prompt
    )

    return response.choices[0].message.content.strip()


def print_sessions(current_session):
    sessions = get_all_sessions_with_titles()

    if not sessions:
        print("No sessions found.\n")
        return

    print("\nSessions:")
    for session_id, title in sessions:
        name = title if title else session_id
        marker = " (current)" if session_id == current_session else ""
        print(f"- {name} [{session_id}]{marker}")
    print()


def print_history(session_id):
    history = get_recent_messages(session_id, limit=20)

    if not history:
        print("No chat history found.\n")
        return

    print(f"\nRecent chat history for session: {session_id}")
    for message in history:
        speaker = "You" if message["role"] == "user" else "AI"
        print(f"{speaker}: {message['content']}")
    print()


def main():
    init_db()

    current_session = get_initial_session()
    create_session(current_session)

    print("Local AI CLI Chatbot started.")
    print("Commands: /new, /list, /switch <session_id>, /history, /rename <title>, /delete <session_id>, exit")
    print(f"Current session: {current_session}\n")

    while True:
        user_input = input(f"[{current_session}] You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if user_input == "/list":
            print_sessions(current_session)
            continue

        if user_input == "/history":
            print_history(current_session)
            continue

        if user_input == "/new":
            current_session = generate_new_session_id()
            create_session(current_session)
            print(f"Switched to new session: {current_session}\n")
            continue

        if user_input.startswith("/switch "):
            target = user_input.split(maxsplit=1)[1].strip()
            sessions = get_all_sessions()

            if target not in sessions:
                print("Session not found.\n")
            else:
                current_session = target
                print(f"Switched to session: {current_session}\n")

            continue

        if user_input.startswith("/rename "):
            new_title = user_input.split(maxsplit=1)[1].strip()

            if not new_title:
                print("Please provide a title.\n")
            else:
                update_session_title(current_session, new_title)
                print(f"Renamed current session to: {new_title}\n")

            continue

        if user_input.startswith("/delete "):
            target_session = user_input.split(maxsplit=1)[1].strip()

            if not session_exists(target_session):
                print("Session not found.\n")
                continue

            delete_session(target_session)

            if target_session == current_session:
                remaining_sessions = get_all_sessions()
                current_session = remaining_sessions[-1] if remaining_sessions else "session_1"
                create_session(current_session)

            print(f"Deleted session: {target_session}\n")
            continue

        if not user_input:
            print("Please enter something.\n")
            continue

        save_message(current_session, "user", user_input)

        history = get_recent_messages(current_session, limit=1)
        if len(history) == 1:
            title = generate_session_title(user_input)
            update_session_title(current_session, title)

        messages = build_messages(current_session)

        try:
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                stream=True
            )

            print("AI: ", end="", flush=True)
            answer_parts = []

            for chunk in stream:
                delta = chunk.choices[0].delta
                content = delta.content or ""

                if content:
                    print(content, end="", flush=True)
                    answer_parts.append(content)

            answer = "".join(answer_parts)
            print("\n")

            save_message(current_session, "assistant", answer)

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()