"""Ingest every document in synthetic-data/documents into the vector store."""
from pathlib import Path

from app.rag.embeddings import EmbeddingService
from app.rag.ingestion import IngestionService
from app.rag.retrieval import VectorStore

CORPUS = Path("synthetic-data/documents")


def main() -> None:
    service = IngestionService(embeddings=EmbeddingService(), store=VectorStore())
    total = 0
    for path in sorted(CORPUS.glob("*.md")):
        count = service.ingest_file(path, source=path.name)
        print(f"{path.name}: {count} chunks")
        total += count
    print(f"Done: {total} chunks ingested.")


if __name__ == "__main__":
    main()
