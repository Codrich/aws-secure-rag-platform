# Architecture Decision: pgvector vs. OpenSearch Serverless

**Decision (v1): PostgreSQL + pgvector.**

## Rationale

pgvector demonstrates the same RAG capabilities - embeddings, cosine
similarity search with HNSW indexing, metadata filtering, private
connectivity, encryption at rest, automated backups - without the always-on
OCU cost floor of OpenSearch Serverless.

## When to revisit

OpenSearch Serverless is the recommended alternative for: high ingest
throughput, hybrid lexical + vector search, or native Bedrock Knowledge Base
integration. The retrieval interface (`app/rag/retrieval.py`) is the seam:
swapping stores means implementing the same search/upsert contract.
