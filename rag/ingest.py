from uuid import uuid4

from rag.chunking import chunk_text
from rag.embedding import EmbeddingService
from rag.loaders import load_documents
from rag.vector_store import VectorStore


def run_ingestion() -> None:
    documents = load_documents()

    if not documents:
        print("No supported documents found in the knowledge directory.")
        return

    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    ids = []
    chunks = []
    embeddings = []
    metadatas = []

    for document in documents:
        document_chunks = chunk_text(document["content"])

        for index, chunk in enumerate(document_chunks):
            chunk_id = str(uuid4())
            embedding = embedding_service.embed_text(chunk)

            ids.append(chunk_id)
            chunks.append(chunk)
            embeddings.append(embedding)
            metadatas.append(
                {
                    "source": document["source"],
                    "filename": document["filename"],
                    "chunk_index": index,
                }
            )

    if not ids:
        print("No chunks were generated from the loaded documents.")
        return

    vector_store.add_documents(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Ingestion completed successfully. Stored {len(ids)} chunks.")


if __name__ == "__main__":
    run_ingestion()