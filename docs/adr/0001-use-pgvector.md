# ADR 0001: Use PostgreSQL + pgvector as the vector store

Status: Accepted (implemented)

## Context
The platform needs similarity search over document-chunk embeddings with
private connectivity, encryption, and backups.

## Decision
PostgreSQL with pgvector (HNSW, cosine distance). Local dev runs
`pgvector/pgvector:pg16`; AWS runs RDS PostgreSQL.

## Alternatives
OpenSearch Serverless: native Bedrock Knowledge Base integration and hybrid
search, but an always-on OCU cost floor (~hundreds of USD/month) unsuited to
an ephemeral, reproducible project.

## Consequences
Retrieval interface (`app/rag/retrieval.py`) is the seam for swapping stores.
Scale ceiling accepted and documented in VECTOR_STORE_DECISION.md.

## Security impact
Single encrypted data store; simpler network and IAM surface.

## Cost impact
Near-zero locally; RDS only during ephemeral deployments.
