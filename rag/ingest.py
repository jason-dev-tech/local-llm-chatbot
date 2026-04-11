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
    source_chunk_counts = {}

    for document in documents:
        document_chunks = chunk_text(document["content"])
        source_label = document.get("filename") or document.get("source") or "unknown"
        source_type = document.get("source_type") or "unknown"
        source_key = (str(source_label), str(source_type))
        source_chunk_counts[source_key] = source_chunk_counts.get(source_key, 0) + len(document_chunks)

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
                }
            )

    if not ids:
        print("No chunks were generated from the loaded documents.")
        return

    for (source_label, source_type), count in source_chunk_counts.items():
        print(f"[ingest] source={source_label} source_type={source_type} chunks={count}")

    vector_store.add_documents(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Ingestion completed successfully. Stored {len(ids)} chunks.")


if __name__ == "__main__":
    run_ingestion()
