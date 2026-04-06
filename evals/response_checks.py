import re

from chat_service import append_sources_to_answer, apply_inline_citations


INLINE_CITATION_PATTERN = re.compile(r"\[\d+\]")
SOURCES_SECTION_PATTERN = re.compile(r"(?:^|\n\n)Sources:\n- \[\d+\] .+", re.DOTALL)


def build_deterministic_rag_answer(chunks: list[dict]) -> str:
    snippets = []

    for chunk in chunks:
        content = chunk.get("content", "").strip()
        if not content:
            continue

        snippets.append(content.splitlines()[0].strip())
        if len(snippets) == 2:
            break

    if not snippets:
        return ""

    return "\n\n".join(snippets)


def build_rag_eval_response(chunks: list[dict]) -> str:
    answer = build_deterministic_rag_answer(chunks)
    answer = apply_inline_citations(answer, chunks)
    return append_sources_to_answer(answer, chunks)


def has_sources_section(text: str) -> bool:
    return bool(SOURCES_SECTION_PATTERN.search(text))


def has_inline_citations(text: str) -> bool:
    main_content = text.split("\n\nSources:\n", maxsplit=1)[0]
    return bool(INLINE_CITATION_PATTERN.search(main_content))
