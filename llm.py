from openai import OpenAI
from config import BASE_URL, API_KEY, MODEL_NAME

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)


def generate_response(messages):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
    )
    return response.choices[0].message.content or ""


def stream_response(messages):
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        content = delta.content if delta and delta.content else ""
        if content:
            yield content


def generate_session_title(user_message):
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "Generate a short and concise title for a chat session based on the user's first message. "
                "Return only the title, with no quotes or extra explanation. Keep it under 8 words."
            ),
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=prompt_messages,
    )

    return (response.choices[0].message.content or "New Chat").strip()