from pathlib import Path

from config import KNOWLEDGE_DIR
from rag.source_metadata import build_source_metadata


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_text_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def load_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def load_documents() -> list[dict]:
    knowledge_path = Path(KNOWLEDGE_DIR)
    documents = []

    for file_path in sorted(knowledge_path.rglob("*")):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        if suffix == ".txt":
            content = load_text_file(file_path)
        elif suffix == ".md":
            content = load_markdown_file(file_path)
        else:
            continue

        source_metadata = build_source_metadata(file_path)
        documents.append({**source_metadata, "content": content})

    return documents
