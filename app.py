from openai import OpenAI
from config import MODEL_NAME, BASE_URL, API_KEY, SESSION_ID
from db import init_db, save_message, get_recent_messages

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

SYSTEM_PROMPT = "You are a helpful assistant. Answer clearly and concisely."


def build_messages():
    history = get_recent_messages(SESSION_ID, limit=10)
    return [{"role": "system", "content": SYSTEM_PROMPT}] + history


def print_history():
    history = get_recent_messages(SESSION_ID, limit=20)

    if not history:
        print("No chat history found.\n")
        return

    print("\nRecent chat history:")
    for message in history:
        speaker = "You" if message["role"] == "user" else "AI"
        print(f"{speaker}: {message['content']}")
    print()


def main():
    init_db()

    print("Local AI CLI Chatbot started.")
    print("Commands: /history, exit\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if user_input == "/history":
            print_history()
            continue

        if not user_input:
            print("Please enter something.\n")
            continue

        save_message(SESSION_ID, "user", user_input)
        messages = build_messages()

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

            save_message(SESSION_ID, "assistant", answer)

        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()