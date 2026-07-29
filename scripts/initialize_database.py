"""Create the pgvector extension, chunk table, and HNSW index."""
from app.rag.retrieval import VectorStore


def main() -> None:
    VectorStore().initialize()
    print("Database initialized: extension, document_chunks table, HNSW index.")


if __name__ == "__main__":
    main()
