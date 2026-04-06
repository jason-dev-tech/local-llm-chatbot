import re

from tools.base import Tool


SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")


def summarize_text(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return ""

    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(normalized) if sentence.strip()]
    if not sentences:
        return normalized[:200].strip()

    summary = " ".join(sentences[:2]).strip()
    if len(summary) <= 240:
        return summary

    return summary[:237].rstrip() + "..."


summarize_text_tool = Tool(
    name="summarize_text",
    function=summarize_text,
)
