from langchain_chroma import Chroma

from config import CHROMA_PERSIST_DIR, RAG_COLLECTION_NAME
from rag.embedding import EmbeddingService
from rag.source_metadata import resolve_chunk_source


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


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[dict]:
    vector_store = _get_vector_store()
    scored_documents = vector_store.similarity_search_with_score(query, k=top_k)

    chunks = []

    for document, distance in scored_documents:
        metadata = document.metadata or {}
        source = resolve_chunk_source({"metadata": metadata})
        chunks.append(
            {
                "content": document.page_content,
                "metadata": metadata,
                "distance": distance,
                "source": source,
            }
        )

    return chunks


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
