from openai import OpenAI
from config import MODEL_NAME, BASE_URL, API_KEY, SESSION_ID
from db import init_db, save_message, get_recent_messages

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

def main():
    init_db()

    print("Local AI CLI Chatbot started. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            print("Please enter something.\n")
            continue

        save_message(SESSION_ID, "user", user_input)

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer clearly and concisely."
            }
        ] + get_recent_messages(SESSION_ID, limit=10)

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages
            )

            answer = response.choices[0].message.content
            print(f"AI: {answer}\n")

            save_message(SESSION_ID, "assistant", answer)

        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    main()