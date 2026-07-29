"""pgvector-backed retrieval with tenant isolation.

Two independent layers enforce isolation (ADR 0002):

1. Application layer - every query filters on tenant_id and the caller's
   allowed classifications inside the SQL WHERE clause, so unauthorized
   chunks are never fetched into application memory.
2. Database layer - PostgreSQL row-level security, FORCEd so it applies to
   the table owner too. Each connection sets `app.tenant_id` via
   set_config(); when it is unset the policy matches nothing, so a coding
   mistake fails closed rather than leaking rows.

Vectors and identifiers are always passed as query parameters - no SQL is
built from caller-controlled strings.
"""
from dataclasses import dataclass
from typing import Any

import psycopg

from app.auth.permissions import Classification
from app.auth.tenancy import TenantContext
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
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS tenant_id TEXT;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS classification TEXT;
UPDATE document_chunks SET tenant_id = 'unassigned' WHERE tenant_id IS NULL;
UPDATE document_chunks SET classification = 'restricted' WHERE classification IS NULL;
ALTER TABLE document_chunks ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE document_chunks ALTER COLUMN classification SET NOT NULL;

ALTER TABLE document_chunks DROP CONSTRAINT IF EXISTS document_chunks_source_chunk_index_key;
CREATE UNIQUE INDEX IF NOT EXISTS document_chunks_tenant_source_idx
    ON document_chunks (tenant_id, source, chunk_index);
CREATE INDEX IF NOT EXISTS document_chunks_tenant_class_idx
    ON document_chunks (tenant_id, classification);
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Row-level security: the database enforces isolation independently of the
-- application. FORCE makes the policy apply to the table owner as well.
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON document_chunks;
CREATE POLICY tenant_isolation ON document_chunks
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));
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

    def _connect_as(self, tenant_id: str) -> psycopg.Connection[Any]:
        """Open a connection scoped to a tenant for the current transaction."""
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.tenant_id', %s, true)", (tenant_id,))
        return conn

    def initialize(self) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(SCHEMA_SQL.replace("%(dims)s", str(self._settings.embedding_dimensions)))

    def upsert_chunks(
        self,
        tenant_id: str,
        source: str,
        classification: Classification,
        chunks: list[tuple[int, str, list[float]]],
    ) -> int:
        with self._connect_as(tenant_id) as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE tenant_id = %s AND source = %s",
                (tenant_id, source),
            )
            for index, content, embedding in chunks:
                cur.execute(
                    "INSERT INTO document_chunks "
                    "(tenant_id, source, chunk_index, content, classification, embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s::vector)",
                    (
                        tenant_id,
                        source,
                        index,
                        content,
                        classification.value,
                        _vector_literal(embedding),
                    ),
                )
        return len(chunks)

    def search(
        self,
        embedding: list[float],
        context: TenantContext,
        top_k: int | None = None,
        min_score: float | None = None,
    ) -> list[RetrievedChunk]:
        """Return chunks for this tenant that the caller's role may read."""
        k = top_k or self._settings.retrieval_top_k
        threshold = min_score if min_score is not None else self._settings.retrieval_min_score
        classifications = sorted(c.value for c in context.allowed_classifications)
        if not classifications:
            return []
        vector = _vector_literal(embedding)
        with self._connect_as(context.tenant_id) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT source, chunk_index, content, "
                "1 - (embedding <=> %s::vector) AS score "
                "FROM document_chunks "
                "WHERE tenant_id = %s AND classification = ANY(%s) "
                "ORDER BY embedding <=> %s::vector "
                "LIMIT %s",
                (vector, context.tenant_id, classifications, vector, k),
            )
            rows = cur.fetchall()
        return [
            RetrievedChunk(source=r[0], chunk_index=r[1], content=r[2], score=float(r[3]))
            for r in rows
            if float(r[3]) >= threshold
        ]
