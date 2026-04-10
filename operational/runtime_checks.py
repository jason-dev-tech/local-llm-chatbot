import importlib
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from config import (
    API_KEY,
    BASE_URL,
    CHROMA_PERSIST_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DB_PATH,
    EMBEDDING_MODEL,
    KNOWLEDGE_DIR,
    MODEL_NAME,
)
from db import init_db


REQUIRED_IMPORTS = (
    "fastapi",
    "openai",
    "chromadb",
    "langchain_chroma",
    "pypdf",
)


def validate_runtime_config() -> list[str]:
    errors = []

    required_values = {
        "MODEL_NAME": MODEL_NAME,
        "OPENAI_BASE_URL": BASE_URL,
        "OPENAI_API_KEY": API_KEY,
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
        "DB_PATH": DB_PATH,
        "KNOWLEDGE_DIR": KNOWLEDGE_DIR,
        "CHROMA_PERSIST_DIR": CHROMA_PERSIST_DIR,
    }

    for name, value in required_values.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{name} must be a non-empty string")

    parsed_base_url = urlparse(BASE_URL)
    if parsed_base_url.scheme not in {"http", "https"} or not parsed_base_url.netloc:
        errors.append("OPENAI_BASE_URL must be a valid http or https URL")

    if CHUNK_SIZE <= 0:
        errors.append("CHUNK_SIZE must be greater than 0")

    if CHUNK_OVERLAP < 0:
        errors.append("CHUNK_OVERLAP must be greater than or equal to 0")

    if CHUNK_OVERLAP >= CHUNK_SIZE:
        errors.append("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

    return errors


def run_backend_smoke_checks() -> dict:
    checks = {}
    config_errors = validate_runtime_config()
    checks["config_valid"] = not config_errors

    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
            checks[f"import:{module_name}"] = True
        except Exception:
            checks[f"import:{module_name}"] = False

    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        checks["database"] = True
    except sqlite3.Error:
        checks["database"] = False

    checks["knowledge_dir"] = Path(KNOWLEDGE_DIR).exists()

    try:
        Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        checks["chroma_dir"] = Path(CHROMA_PERSIST_DIR).exists()
    except OSError:
        checks["chroma_dir"] = False

    overall_ok = all(checks.values()) and not config_errors

    return {
        "ok": overall_ok,
        "checks": checks,
        "config_errors": config_errors,
    }
