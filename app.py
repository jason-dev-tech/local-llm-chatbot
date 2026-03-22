from db import init_db, get_all_sessions_with_titles, get_recent_messages, create_session
from chat_service import (
    get_initial_session,
    create_new_session,
    switch_session,
    rename_session,
    remove_session,
    send_message_and_stream,
)


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
            current_session = create_new_session()
            print(f"Switched to new session: {current_session}\n")
            continue

        if user_input.startswith("/switch "):
            target = user_input.split(maxsplit=1)[1].strip()
            switched = switch_session(target)

            if not switched:
                print("Session not found.\n")
            else:
                current_session = switched
                print(f"Switched to session: {current_session}\n")

            continue

        if user_input.startswith("/rename "):
            new_title = user_input.split(maxsplit=1)[1].strip()

            if not new_title:
                print("Please provide a title.\n")
            else:
                rename_session(current_session, new_title)
                print(f"Renamed current session to: {new_title}\n")

            continue

        if user_input.startswith("/delete "):
            target_session = user_input.split(maxsplit=1)[1].strip()
            deleted = remove_session(target_session)

            if not deleted:
                print("Session not found.\n")
                continue

            if target_session == current_session:
                remaining_sessions = get_all_sessions_with_titles()
                if remaining_sessions:
                    current_session = remaining_sessions[-1][0]
                else:
                    current_session = "session_1"
                    create_session(current_session)

            print(f"Deleted session: {target_session}\n")
            continue

        if not user_input:
            print("Please enter something.\n")
            continue

        try:
            print("AI: ", end="", flush=True)

            for token in send_message_and_stream(current_session, user_input):
                print(token, end="", flush=True)

            print("\n")

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()