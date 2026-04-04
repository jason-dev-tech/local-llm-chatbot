"""Minimal LangChain wrapper for the local OpenAI-compatible chat model."""

from langchain_openai import ChatOpenAI

import config


def get_langchain_chat_model() -> ChatOpenAI:
    """Return a configured LangChain chat model."""
    temperature = getattr(
        config,
        "TEMPERATURE",
        getattr(config, "MODEL_TEMPERATURE", 0.7),
    )
    return ChatOpenAI(
        model=config.MODEL_NAME,
        base_url=config.BASE_URL,
        api_key=config.API_KEY,
        temperature=temperature,
    )


def generate_langchain_response(user_message: str) -> str:
    """Generate a plain-text response for a single user message."""
    response = get_langchain_chat_model().invoke(user_message)
    content = response.content

    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        parts = [
            item.get("text", "").strip()
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        text = "\n".join(part for part in parts if part)
    else:
        text = ""

    if not text:
        raise ValueError("LangChain response content is empty.")

    return text
