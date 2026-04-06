from pathlib import Path

from config import KNOWLEDGE_DIR


def build_source_metadata(file_path: Path) -> dict[str, str]:
    knowledge_root = Path(KNOWLEDGE_DIR).resolve()
    resolved_file_path = file_path.resolve()

    try:
        relative_path = resolved_file_path.relative_to(knowledge_root)
        source = relative_path.as_posix()
    except ValueError:
        source = file_path.name

    return {
        "source": source,
        "filename": file_path.name,
    }


def resolve_chunk_source(chunk: dict) -> str:
    metadata = chunk.get("metadata", {})
    source = (
        chunk.get("source")
        or metadata.get("source")
        or metadata.get("filename")
        or "unknown"
    )

    if not isinstance(source, str):
        return "unknown"

    normalized_source = source.strip().replace("\\", "/")
    if not normalized_source:
        return "unknown"

    return normalized_source.lstrip("./")
