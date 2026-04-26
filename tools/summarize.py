import re

from tools.base import Tool


SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
SUMMARY_PROMPT_TEMPLATE = (
    "Summarize the text below.\n"
    "Requirements:\n"
    "- Cover all major points in the input.\n"
    "- Include information from the entire text, not just the beginning.\n"
    "- Preserve distinct topics and important details.\n"
    "- Produce a balanced, concise summary.\n"
    "- Do not add new facts.\n"
    "- Return only the summary.\n\n"
    "Text:\n{text}"
)


def _balanced_extractive_summary(sentences: list[str]) -> str:
    if len(sentences) <= 2:
        return " ".join(sentences).strip()

    selected_indexes = [0, len(sentences) // 2, len(sentences) - 1]
    selected = []
    for index in selected_indexes:
        sentence = sentences[index]
        if sentence not in selected:
            selected.append(sentence)

    return " ".join(selected).strip()


def summarize_text(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return ""

    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(normalized) if sentence.strip()]
    if not sentences:
        return normalized[:200].strip()

    if len(sentences) <= 2:
        summary = " ".join(sentences).strip()
    else:
        try:
            from llm_langchain import generate_langchain_response

            summary = generate_langchain_response(
                SUMMARY_PROMPT_TEMPLATE.format(text=normalized)
            ).strip()
        except Exception:
            summary = _balanced_extractive_summary(sentences)

    if len(summary) <= 240:
        return summary

    return summary[:237].rstrip() + "..."


summarize_text_tool = Tool(
    name="summarize_text",
    function=summarize_text,
)
