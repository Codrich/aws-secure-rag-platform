"""pgvector-backed retrieval.

Cosine similarity search over document chunks. Connections use the
configured DATABASE_URL (Secrets Manager in production). Vectors are
passed as parameterized values and cast server-side - no SQL built from
user input.
"""
from dataclasses import dataclass
from typing import Any

import psycopg

from app.core.config import get_settings

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(%(dims)s) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, chunk_index)
);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops);
"""


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    chunk_index: int
    content: str
    score: float


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"


class VectorStore:
    def __init__(self, conninfo: str | None = None) -> None:
        settings = get_settings()
        self._conninfo = conninfo or settings.database_url
        self._settings = settings

    def _connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self._conninfo)

    def initialize(self) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                SCHEMA_SQL.replace("%(dims)s", str(self._settings.embedding_dimensions))
            )

    def upsert_chunks(
        self, source: str, chunks: list[tuple[int, str, list[float]]]
    ) -> int:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM document_chunks WHERE source = %s", (source,))
            for index, content, embedding in chunks:
                cur.execute(
                    "INSERT INTO document_chunks (source, chunk_index, content, embedding) "
                    "VALUES (%s, %s, %s, %s::vector)",
                    (source, index, content, _vector_literal(embedding)),
                )
        return len(chunks)

    def search(
        self, embedding: list[float], top_k: int | None = None, min_score: float | None = None
    ) -> list[RetrievedChunk]:
        k = top_k or self._settings.retrieval_top_k
        threshold = min_score if min_score is not None else self._settings.retrieval_min_score
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT source, chunk_index, content, "
                "1 - (embedding <=> %s::vector) AS score "
                "FROM document_chunks "
                "ORDER BY embedding <=> %s::vector "
                "LIMIT %s",
                (_vector_literal(embedding), _vector_literal(embedding), k),
            )
            rows = cur.fetchall()
        return [
            RetrievedChunk(source=r[0], chunk_index=r[1], content=r[2], score=float(r[3]))
            for r in rows
            if float(r[3]) >= threshold
        ]
