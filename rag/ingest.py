from uuid import uuid4

from rag.chunking import chunk_text
from rag.embedding import EmbeddingService
from rag.loaders import load_documents
from rag.vector_store import VectorStore


def ingest_documents(documents: list[dict], extra_metadata: dict | None = None) -> int:
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    extra_metadata = extra_metadata or {}

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
                    **(
                        {"title": document["title"]}
                        if "title" in document
                        else {}
                    ),
                    **(
                        {"source_type": document["source_type"]}
                        if "source_type" in document
                        else {}
                    ),
                    **(
                        {"record_id": document["record_id"]}
                        if "record_id" in document
                        else {}
                    ),
                    **(
                        {"record_title": document["record_title"]}
                        if "record_title" in document
                        else {}
                    ),
                    **(
                        {"record_index": document["record_index"]}
                        if "record_index" in document
                        else {}
                    ),
                    **(
                        {"record_type": document["record_type"]}
                        if "record_type" in document
                        else {}
                    ),
                    **(
                        {"endpoint_url": document["endpoint_url"]}
                        if "endpoint_url" in document
                        else {}
                    ),
                    **(
                        {"page_number": document["page_number"]}
                        if "page_number" in document
                        else {}
                    ),
                    **extra_metadata,
                }
            )

    if not ids:
        return 0

    vector_store.add_documents(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(ids)


def run_ingestion() -> None:
    documents = load_documents()

    if not documents:
        print("No supported documents found in the knowledge directory.")
        return

    stored_count = ingest_documents(documents)
    if not stored_count:
        print("No chunks were generated from the loaded documents.")
        return

    print(f"Ingestion completed successfully. Stored {stored_count} chunks.")


if __name__ == "__main__":
    run_ingestion()
