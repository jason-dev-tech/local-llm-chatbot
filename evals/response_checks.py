import re

from chat_service import append_sources_to_answer, apply_inline_citations


INLINE_CITATION_PATTERN = re.compile(r"\[\d+\]")
SOURCES_SECTION_PATTERN = re.compile(r"(?:^|\n\n)Sources:\n- \[\d+\] .+", re.DOTALL)
SOURCE_LINE_PATTERN = re.compile(r"^- \[(\d+)\] (.+)$", re.MULTILINE)


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


def extract_inline_citation_numbers(text: str) -> list[int]:
    main_content = text.split("\n\nSources:\n", maxsplit=1)[0]
    return [int(match.group(0).strip("[]")) for match in INLINE_CITATION_PATTERN.finditer(main_content)]


def extract_source_entries(text: str) -> list[dict]:
    entries = []

    for match in SOURCE_LINE_PATTERN.finditer(text):
        entries.append(
            {
                "number": int(match.group(1)),
                "label": match.group(2).strip(),
            }
        )

    return entries


def count_distinct_sources(chunks: list[dict]) -> int:
    return len(
        {
            chunk.get("source") or chunk.get("metadata", {}).get("source")
            for chunk in chunks
            if chunk.get("source") or chunk.get("metadata", {}).get("source")
        }
    )


def source_labels_are_clean(text: str) -> bool:
    entries = extract_source_entries(text)
    if not entries:
        return False

    for entry in entries:
        label = entry["label"]
        if not label or label.lower() == "unknown":
            return False
        if "/" in label or "\\" in label:
            return False

    return True


def citations_reference_known_sources(text: str) -> bool:
    citation_numbers = set(extract_inline_citation_numbers(text))
    source_numbers = {entry["number"] for entry in extract_source_entries(text)}

    if not citation_numbers:
        return False

    return citation_numbers.issubset(source_numbers)
