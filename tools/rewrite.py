import re

from tools.base import Tool


WHITESPACE_PATTERN = re.compile(r"\s+")
REWRITE_PREFIX_PATTERN = re.compile(
    r"^(?:rewrite:|rewrite this:|rewrite this clearly:|rewrite this to sound clearer:|make this clearer:|improve this sentence:)\s*",
    re.IGNORECASE,
)


def _normalize_text(text: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", text.strip())


def rewrite_text(text: str) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return ""

    cleaned = REWRITE_PREFIX_PATTERN.sub("", normalized).strip()
    if not cleaned:
        return ""

    prompt = (
        "Rewrite the text for clarity.\n"
        "Rules:\n"
        "- Preserve the original meaning.\n"
        "- Do not add new facts.\n"
        "- Do not expand unnecessarily.\n"
        "- Fix grammar and wording when helpful.\n"
        "- Return only the rewritten text.\n\n"
        f"Text:\n{cleaned}"
    )

    try:
        from llm_langchain import generate_langchain_response

        rewritten = _normalize_text(generate_langchain_response(prompt))
        return rewritten or cleaned
    except Exception:
        return cleaned


rewrite_text_tool = Tool(
    name="rewrite_text",
    function=rewrite_text,
)
