"""Document ingestion: read -> chunk -> embed -> upsert.

Phase 3 moves this behind S3 -> SQS with a DLQ; the pipeline stages and
their contracts stay the same.
"""
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.rag.chunking import chunk_text
from app.rag.embeddings import EmbeddingService
from app.rag.retrieval import VectorStore

logger = get_logger(__name__)


class IngestionService:
    def __init__(self, embeddings: EmbeddingService, store: VectorStore) -> None:
        self._embeddings = embeddings
        self._store = store
        self._settings = get_settings()

    def ingest_text(self, source: str, text: str) -> int:
        chunks = chunk_text(
            text,
            max_chars=self._settings.chunk_max_chars,
            overlap_chars=self._settings.chunk_overlap_chars,
        )
        rows: list[tuple[int, str, list[float]]] = []
        for chunk in chunks:
            rows.append((chunk.index, chunk.text, self._embeddings.embed(chunk.text)))
        count = self._store.upsert_chunks(source, rows)
        logger.info("document_ingested", source=source, chunks=count)
        return count

    def ingest_file(self, path: Path, source: str | None = None) -> int:
        return self.ingest_text(source or path.name, path.read_text(encoding="utf-8"))
