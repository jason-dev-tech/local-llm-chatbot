import json
import re

from tools.base import Tool


EMPTY_EXTRACTION = {
    "query_type": "unknown",
    "topics": [],
    "technologies": [],
    "files": [],
    "constraints": [],
    "requested_operation": "unknown",
}

JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
FILE_PATTERN = re.compile(r"\b[\w.-]+\.[A-Za-z0-9]+\b")
TOKEN_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9.+_-]*\b")
INFORMATIVE_CHARACTER_PATTERN = re.compile(r"[A-Za-z0-9]")
VALID_QUERY_TYPES = {
    "knowledge_lookup",
    "comparison",
    "summarization",
    "rewrite",
    "general_chat",
    "unknown",
}
VALID_REQUESTED_OPERATIONS = {
    "lookup",
    "compare",
    "summarize",
    "rewrite",
    "extract",
    "chat",
    "unknown",
}
KNOWN_TECHNOLOGIES = {
    "rag",
    "langchain",
    "chroma",
    "fastapi",
    "react",
    "vite",
    "sqlite",
    "python",
    "typescript",
    "openai",
}
KNOWN_TOPICS = {
    "citations",
    "citation",
    "retrieval",
    "routing",
    "semantic",
    "search",
    "knowledge",
    "context",
    "entities",
}
CONSTRAINT_PREFIXES = ("about ", "using ", "with ")


def _find_cased_value(source_text: str, value: str) -> str:
    pattern = re.compile(rf"\b{re.escape(value)}\b", re.IGNORECASE)
    match = pattern.search(source_text)
    return match.group(0) if match else value


def _normalize_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        return dict(EMPTY_EXTRACTION)

    normalized = dict(EMPTY_EXTRACTION)
    for key in ("topics", "technologies", "files", "constraints"):
        value = payload.get(key, [])
        normalized[key] = value if isinstance(value, list) else []

    query_type = payload.get("query_type", "unknown")
    requested_operation = payload.get("requested_operation", "unknown")

    normalized["query_type"] = (
        query_type if isinstance(query_type, str) and query_type in VALID_QUERY_TYPES else "unknown"
    )
    normalized["requested_operation"] = (
        requested_operation
        if isinstance(requested_operation, str) and requested_operation in VALID_REQUESTED_OPERATIONS
        else "unknown"
    )

    return normalized


def _extract_json_object(text: str) -> dict | None:
    match = JSON_BLOCK_PATTERN.search(text)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _unique_preserving_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _normalize_extracted_categories(payload: dict, source_text: str) -> dict:
    technologies = []
    topics = []

    for value in payload.get("technologies", []):
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped:
            continue

        lowered = stripped.lower()
        if lowered in KNOWN_TOPICS:
            topics.append(lowered)
        else:
            technologies.append(_find_cased_value(source_text, stripped))

    for value in payload.get("topics", []):
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped:
            continue

        lowered = stripped.lower()
        if lowered in KNOWN_TECHNOLOGIES:
            technologies.append(_find_cased_value(source_text, stripped))
        else:
            topics.append(lowered)

    payload["technologies"] = _unique_preserving_order(technologies)
    payload["topics"] = _unique_preserving_order(topics)
    return payload


def _deterministic_extract(text: str) -> dict:
    lowered = text.lower()
    query_type = "unknown"
    requested_operation = "unknown"

    if "compare" in lowered:
        query_type = "comparison"
        requested_operation = "compare"
    elif "summarize" in lowered or "summary" in lowered:
        query_type = "summarization"
        requested_operation = "summarize"
    elif "rewrite" in lowered or "rephrase" in lowered:
        query_type = "rewrite"
        requested_operation = "rewrite"
    elif any(term in lowered for term in ("knowledge", "rag", "document", "documents", "semantic search")):
        query_type = "knowledge_lookup"
        requested_operation = "lookup"
    elif any(term in lowered for term in ("hello", "hi", "hey", "chat")):
        query_type = "general_chat"
        requested_operation = "chat"
    elif "extract" in lowered:
        requested_operation = "extract"

    technologies = []
    topics = []
    for token in TOKEN_PATTERN.findall(text):
        lowered_token = token.lower()
        if lowered_token in KNOWN_TECHNOLOGIES:
            technologies.append(token)
        elif lowered_token in KNOWN_TOPICS:
            topics.append(lowered_token)

    files = FILE_PATTERN.findall(text)

    constraints = []
    for prefix in CONSTRAINT_PREFIXES:
        index = lowered.find(prefix)
        if index != -1:
            constraints.append(text[index:].strip())

    return _normalize_payload(
        {
            "query_type": query_type,
            "topics": _unique_preserving_order(topics),
            "technologies": _unique_preserving_order(technologies),
            "files": _unique_preserving_order(files),
            "constraints": _unique_preserving_order(constraints),
            "requested_operation": requested_operation,
        }
    )


def extract_entities(text: str) -> str:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return json.dumps(dict(EMPTY_EXTRACTION))
    if not INFORMATIVE_CHARACTER_PATTERN.search(normalized):
        return json.dumps(dict(EMPTY_EXTRACTION))

    prompt = (
        "Extract structured query signals from the user text.\n"
        "Return JSON only.\n"
        "Do not add explanation.\n"
        "Do not invent entities or constraints.\n"
        "Use empty arrays when absent.\n"
        "Preserve original casing for technologies and filenames where possible.\n"
        "Field definitions:\n"
        "- topics: subject areas, concepts, or content themes.\n"
        "- technologies: concrete technologies, frameworks, tools, or named technical methods.\n"
        "- files: explicit filenames only.\n"
        "- constraints: explicit qualifiers, scope limits, or filters stated in the text.\n"
        'query_type must be one of: knowledge_lookup, comparison, summarization, rewrite, general_chat, unknown.\n'
        'requested_operation must be one of: lookup, compare, summarize, rewrite, extract, chat, unknown.\n'
        "Use this schema exactly:\n"
        '{\n'
        '  "query_type": "",\n'
        '  "topics": [],\n'
        '  "technologies": [],\n'
        '  "files": [],\n'
        '  "constraints": [],\n'
        '  "requested_operation": ""\n'
        '}\n\n'
        f"User text:\n{normalized}"
    )

    try:
        from llm_langchain import generate_langchain_response

        raw_response = generate_langchain_response(prompt)
        payload = _extract_json_object(raw_response)
        if payload is None:
            return json.dumps(_deterministic_extract(normalized))
        normalized_payload = _normalize_payload(payload)
        normalized_payload = _normalize_extracted_categories(normalized_payload, normalized)
        return json.dumps(normalized_payload)
    except Exception:
        return json.dumps(_deterministic_extract(normalized))


extract_entities_tool = Tool(
    name="extract_entities",
    function=extract_entities,
)
