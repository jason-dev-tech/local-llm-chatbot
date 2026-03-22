from rag.embedding import EmbeddingService
from rag.vector_store import VectorStore


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[dict]:
    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    query_embedding = embedding_service.embed_text(query)
    results = vector_store.query(query_embedding, top_k=top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks = []

    for document, metadata, distance in zip(documents, metadatas, distances):
        chunks.append(
            {
                "content": document,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return chunks


def build_context_text(chunks: list[dict]) -> str:
    if not chunks:
        return ""

    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        source = chunk["metadata"].get("source", "unknown")
        content = chunk["content"]

        context_parts.append(
            f"[Source {index}] {source}\n{content}"
        )

    return "\n\n".join(context_parts)