import re

from langchain_chroma import Chroma

from config import CHROMA_PERSIST_DIR, RAG_COLLECTION_NAME
from rag.embedding import EmbeddingService
from rag.source_metadata import resolve_chunk_source


WORD_PATTERN = re.compile(r"\b[a-z0-9]+\b")


class _EmbeddingAdapter:
    """Adapt the existing embedding service to LangChain's embedding interface."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    def embed_query(self, text: str) -> list[float]:
        return self.embedding_service.embed_text(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embedding_service.embed_text(text) for text in texts]


def _get_vector_store() -> Chroma:
    return Chroma(
        collection_name=RAG_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=_EmbeddingAdapter(),
    )


def _build_filename_filter(file_filters: list[str] | None) -> dict | None:
    if not file_filters:
        return None

    normalized_filters = [value.strip() for value in file_filters if isinstance(value, str) and value.strip()]
    if not normalized_filters:
        return None

    if len(normalized_filters) == 1:
        return {"filename": normalized_filters[0]}

    return {"$or": [{"filename": value} for value in normalized_filters]}


def _combine_filters(*filters: dict | None) -> dict | None:
    active_filters = [value for value in filters if value]
    if not active_filters:
        return None
    if len(active_filters) == 1:
        return active_filters[0]
    return {"$and": active_filters}


def _build_session_filter(session_id: str | None) -> dict | None:
    if not isinstance(session_id, str) or not session_id.strip():
        return None
    return {"session_id": session_id.strip()}


def _is_global_chunk(chunk: dict) -> bool:
    session_id = chunk.get("metadata", {}).get("session_id")
    return not isinstance(session_id, str) or not session_id.strip()


def _tokenize(text: str) -> set[str]:
    return set(WORD_PATTERN.findall(text.lower()))


def _candidate_count(top_k: int) -> int:
    return max(top_k, top_k * 2)


def _build_rerank_text(content: str, metadata: dict, source: str) -> str:
    parts = [
        content,
        metadata.get("filename", ""),
        metadata.get("title", ""),
        source,
    ]
    return " ".join(part for part in parts if isinstance(part, str) and part.strip())


def _score_chunk(query_tokens: set[str], content: str, metadata: dict, source: str, distance: float) -> float:
    candidate_tokens = _tokenize(_build_rerank_text(content, metadata, source))
    lexical_overlap = len(query_tokens & candidate_tokens)
    lexical_score = lexical_overlap / max(len(query_tokens), 1)
    distance_score = 1 / (1 + max(distance, 0))
    return (distance_score * 0.7) + (lexical_score * 0.3)


def _query_chunks(query: str, top_k: int, search_filter: dict | None) -> list[dict]:
    vector_store = _get_vector_store()
    candidate_k = _candidate_count(top_k)
    scored_documents = vector_store.similarity_search_with_score(
        query,
        k=candidate_k,
        filter=search_filter,
    )

    query_tokens = _tokenize(query)
    chunks = []

    for document, distance in scored_documents:
        metadata = document.metadata or {}
        source = resolve_chunk_source({"metadata": metadata})
        content = document.page_content
        chunks.append(
            {
                "content": content,
                "metadata": metadata,
                "distance": distance,
                "source": source,
                "rerank_score": _score_chunk(query_tokens, content, metadata, source, distance),
            }
        )

    chunks.sort(
        key=lambda chunk: (
            -chunk["rerank_score"],
            chunk["distance"],
            chunk["source"],
        )
    )

    return chunks[:top_k]


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 3,
    file_filters: list[str] | None = None,
    session_id: str | None = None,
) -> list[dict]:
    filename_filter = _build_filename_filter(file_filters)
    session_filter = _build_session_filter(session_id)

    if session_filter:
        session_chunks = _query_chunks(
            query,
            top_k,
            _combine_filters(filename_filter, session_filter),
        )
        if session_chunks:
            return session_chunks

        global_candidates = _query_chunks(
            query,
            max(top_k * 4, top_k),
            filename_filter,
        )
        return [chunk for chunk in global_candidates if _is_global_chunk(chunk)][:top_k]

    return _query_chunks(query, top_k, filename_filter)


def build_context_text(chunks: list[dict]) -> str:
    if not chunks:
        return ""

    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        source = resolve_chunk_source(chunk)
        content = chunk["content"]

        context_parts.append(
            f"[Source {index}] {source}\n{content}"
        )

    return "\n\n".join(context_parts)
