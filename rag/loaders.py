import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from config import JSON_API_MANIFEST_PATH, KNOWLEDGE_DIR
from rag.source_metadata import build_source_metadata


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".json"}
STRUCTURED_RECORD_ARRAY_KEYS = ("records", "items", "results")
PRIORITY_FIELD_LABELS = (
    ("record_type", "Record type"),
    ("id", "Record id"),
    ("title", "Title"),
    ("name", "Name"),
)


def load_text_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def load_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def load_json_file(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _is_empty_value(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _normalize_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _flatten_record(record: dict, prefix: str = "") -> list[tuple[str, str]]:
    flattened = []

    for key in sorted(record):
        value = record[key]
        if _is_empty_value(value):
            continue

        flattened_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            flattened.extend(_flatten_record(value, flattened_key))
            continue

        if isinstance(value, list):
            if all(not isinstance(item, (dict, list)) for item in value):
                normalized_items = [
                    _normalize_scalar(item)
                    for item in value
                    if not _is_empty_value(item)
                ]
                if normalized_items:
                    flattened.append((flattened_key, ", ".join(normalized_items)))
            else:
                flattened.append(
                    (
                        flattened_key,
                        json.dumps(value, ensure_ascii=True, sort_keys=True),
                    )
                )
            continue

        flattened.append((flattened_key, _normalize_scalar(value)))

    return flattened


def _extract_records(payload) -> list:
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in STRUCTURED_RECORD_ARRAY_KEYS:
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return [payload]

    return [payload]


def _extract_payload_record_type(payload) -> str | None:
    if not isinstance(payload, dict):
        return None

    value = payload.get("record_type") or payload.get("type")
    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def _coerce_record(record) -> dict:
    if isinstance(record, dict):
        return record

    return {"value": record}


def _detect_record_type(record: dict, default_record_type: str | None = None) -> str | None:
    if default_record_type and default_record_type.strip():
        return default_record_type.strip()

    value = record.get("record_type") or record.get("type")
    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def _extract_record_id(record: dict) -> str | None:
    value = record.get("id")
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


def _extract_record_title(record: dict) -> str | None:
    for key in ("title", "name"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _build_record_content(record: dict, default_record_type: str | None = None) -> tuple[str, dict]:
    lines = []
    used_keys = set()

    record_type = _detect_record_type(record, default_record_type)
    if record_type:
        lines.append(f"Record type: {record_type}")
        used_keys.update({"record_type", "type"})

    record_id = _extract_record_id(record)
    if record_id:
        lines.append(f"Record id: {record_id}")
        used_keys.add("id")

    record_title = _extract_record_title(record)
    if record_title:
        if "title" in record and isinstance(record.get("title"), str) and record["title"].strip():
            lines.append(f"Title: {record_title}")
            used_keys.add("title")
        elif "name" in record and isinstance(record.get("name"), str) and record["name"].strip():
            lines.append(f"Name: {record_title}")
            used_keys.add("name")

    if record_type:
        if record_title:
            lines.append(f"{record_title} is a {record_type}.")
        else:
            lines.append(f"This is a {record_type}.")

    flattened = _flatten_record(record)
    for key, value in flattened:
        root_key = key.split(".", maxsplit=1)[0]
        if root_key in used_keys:
            continue
        lines.append(f"{key}: {value}")

    return "\n".join(lines).strip(), {
        "record_type": record_type,
        "record_id": record_id,
        "record_title": record_title,
    }


def _build_json_documents(
    payload,
    source_metadata: dict[str, str],
    *,
    source_type: str,
    endpoint_url: str | None = None,
    default_record_type: str | None = None,
) -> list[dict]:
    documents = []
    effective_default_record_type = default_record_type or _extract_payload_record_type(payload)

    for record_index, record in enumerate(_extract_records(payload)):
        normalized_record = _coerce_record(record)
        content, record_metadata = _build_record_content(
            normalized_record,
            effective_default_record_type,
        )
        if not content:
            continue

        document = {
            **source_metadata,
            "content": content,
            "source_type": source_type,
            "record_index": record_index,
            **(
                {"record_id": record_metadata["record_id"]}
                if record_metadata["record_id"]
                else {}
            ),
            **(
                {"record_title": record_metadata["record_title"], "title": record_metadata["record_title"]}
                if record_metadata["record_title"]
                else {}
            ),
            **(
                {"record_type": record_metadata["record_type"]}
                if record_metadata["record_type"]
                else {}
            ),
            **(
                {"endpoint_url": endpoint_url}
                if endpoint_url
                else {}
            ),
        }
        documents.append(document)

    return documents


def load_json_documents(file_path: Path) -> list[dict]:
    payload = load_json_file(file_path)
    source_metadata = build_source_metadata(file_path)
    return _build_json_documents(
        payload,
        source_metadata,
        source_type="json_file",
    )


def _build_api_source_metadata(name: str) -> dict[str, str]:
    normalized_name = name.strip().replace("\\", "/").strip("/")
    return {
        "source": f"api/{normalized_name}",
        "filename": f"{normalized_name}.json",
    }


def _derive_api_source_name(url: str) -> str:
    parsed = urlparse(url)
    path = (parsed.path or "").strip("/")
    if path:
        return path.replace("/", "_")
    return parsed.netloc.replace(":", "_") or "api_source"


def load_json_api_documents(manifest_path: Path | None = None) -> list[dict]:
    resolved_manifest_path = (manifest_path or Path(JSON_API_MANIFEST_PATH)).resolve()
    if not resolved_manifest_path.exists():
        return []

    try:
        manifest_payload = json.loads(resolved_manifest_path.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"Skipping JSON API manifest {resolved_manifest_path.name}: failed to parse ({error})")
        return []

    if not isinstance(manifest_payload, list):
        print(f"Skipping JSON API manifest {resolved_manifest_path.name}: expected a list of sources.")
        return []

    documents = []

    for entry_index, entry in enumerate(manifest_payload):
        if not isinstance(entry, dict):
            print(f"Skipping JSON API source at index {entry_index}: expected an object.")
            continue

        url = entry.get("url")
        if not isinstance(url, str) or not url.strip():
            print(f"Skipping JSON API source at index {entry_index}: missing url.")
            continue

        source_name = entry.get("name")
        if not isinstance(source_name, str) or not source_name.strip():
            source_name = _derive_api_source_name(url)

        try:
            with urlopen(url.strip(), timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            print(f"Skipping JSON API source {source_name}: fetch failed ({error})")
            continue

        documents.extend(
            _build_json_documents(
                payload,
                _build_api_source_metadata(source_name),
                source_type="json_api",
                endpoint_url=url.strip(),
                default_record_type=entry.get("record_type") if isinstance(entry.get("record_type"), str) else None,
            )
        )

    return documents


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
                "source_type": "pdf",
                "page_number": page_index,
            }
        )

    return documents


def load_documents() -> list[dict]:
    knowledge_path = Path(KNOWLEDGE_DIR)
    documents = []
    manifest_path = Path(JSON_API_MANIFEST_PATH).resolve()

    for file_path in sorted(knowledge_path.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.resolve() == manifest_path:
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
        elif suffix == ".json":
            documents.extend(load_json_documents(file_path))
            continue
        else:
            continue

        source_metadata = build_source_metadata(file_path)
        documents.append(
            {
                **source_metadata,
                "content": content,
                "source_type": "txt" if suffix == ".txt" else "md",
            }
        )

    documents.extend(load_json_api_documents(manifest_path))

    source_counts = {}
    for document in documents:
        source_label = document.get("filename") or document.get("source") or "unknown"
        source_type = document.get("source_type") or "unknown"
        key = (str(source_label), str(source_type))
        source_counts[key] = source_counts.get(key, 0) + 1

    for (source_label, source_type), count in source_counts.items():
        print(f"[ingest] source={source_label} source_type={source_type} documents={count}")

    return documents
