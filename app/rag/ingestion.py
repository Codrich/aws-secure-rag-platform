"""Document ingestion: read -> chunk -> embed -> upsert, scoped to a tenant.

Milestone 6 moves this behind S3 -> SQS with a DLQ; the pipeline stages and
their contracts stay the same.
"""
from pathlib import Path

from app.auth.permissions import Classification
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

    def ingest_text(
        self, tenant_id: str, source: str, classification: Classification, text: str
    ) -> int:
        chunks = chunk_text(
            text,
            max_chars=self._settings.chunk_max_chars,
            overlap_chars=self._settings.chunk_overlap_chars,
        )
        rows: list[tuple[int, str, list[float]]] = []
        for chunk in chunks:
            rows.append((chunk.index, chunk.text, self._embeddings.embed(chunk.text)))
        count = self._store.upsert_chunks(tenant_id, source, classification, rows)
        logger.info(
            "document_ingested",
            tenant_id=tenant_id,
            source=source,
            classification=classification.value,
            chunks=count,
        )
        return count

    def ingest_file(
        self,
        path: Path,
        tenant_id: str,
        classification: Classification,
        source: str | None = None,
    ) -> int:
        return self.ingest_text(
            tenant_id=tenant_id,
            source=source or path.name,
            classification=classification,
            text=path.read_text(encoding="utf-8"),
        )
