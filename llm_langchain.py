"""Minimal LangChain wrapper for the local OpenAI-compatible chat model."""

from langchain_openai import ChatOpenAI

import config


def _extract_text_content(content: object, *, strip: bool = True) -> str:
    """Normalize LangChain response content to plain text."""
    if isinstance(content, str):
        return content.strip() if strip else content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                if isinstance(text, str):
                    parts.append(text.strip() if strip else text)

        return "\n".join(part for part in parts if part)

    return ""


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
    text = _extract_text_content(response.content)

    if not text:
        raise ValueError("LangChain response content is empty.")

    return text


def stream_langchain_response(user_message: str):
    """Yield plain-text response chunks for a single user message."""
    for chunk in get_langchain_chat_model().stream(user_message):
        text = _extract_text_content(getattr(chunk, "content", ""), strip=False)
        if text:
            yield text
