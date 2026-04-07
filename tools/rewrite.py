from tools.base import Tool


def rewrite_text(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return ""

    return " ".join(normalized.split())


rewrite_text_tool = Tool(
    name="rewrite_text",
    function=rewrite_text,
)
