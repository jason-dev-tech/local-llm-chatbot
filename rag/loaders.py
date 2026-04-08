from pathlib import Path

from config import KNOWLEDGE_DIR
from rag.source_metadata import build_source_metadata


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def load_text_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def load_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def load_pdf_documents(file_path: Path) -> list[dict]:
    try:
        from pypdf import PdfReader
    except Exception as error:
        print(f"Skipping PDF {file_path.name}: PDF parser unavailable ({error})")
        return []

    try:
        reader = PdfReader(str(file_path))
    except Exception as error:
        print(f"Skipping PDF {file_path.name}: failed to parse ({error})")
        return []

    source_metadata = build_source_metadata(file_path)
    documents = []

    for page_index, page in enumerate(reader.pages, start=1):
        try:
            content = (page.extract_text() or "").strip()
        except Exception as error:
            print(
                f"Skipping page {page_index} in {file_path.name}: "
                f"failed to extract text ({error})"
            )
            continue

        if not content:
            continue

        documents.append(
            {
                **source_metadata,
                "content": content,
                "page_number": page_index,
            }
        )

    return documents


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
        elif suffix == ".pdf":
            documents.extend(load_pdf_documents(file_path))
            continue
        else:
            continue

        source_metadata = build_source_metadata(file_path)
        documents.append({**source_metadata, "content": content})

    return documents
