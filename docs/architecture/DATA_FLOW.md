# Data Flow

## Query path (implemented)

1. Client calls `POST /v1/query` with a question (Cognito JWT from Phase 2).
2. Input validation: size limits, control-character sanitization.
3. Question is embedded via Bedrock (Titan Text Embeddings v2).
4. pgvector cosine search returns top-k chunks above the score threshold.
5. No qualifying chunks -> deterministic refusal, **no model call**.
6. Otherwise a grounded prompt (system prompt + numbered context) goes to the
   configured Bedrock model via the Converse API.
7. Response returns with citations (source, chunk index, score) and token counts.
8. Logs carry metadata only (request ID, tokens, latency); prompt/response
   content is never logged outside synthetic-data dev mode.

## Ingestion path (local now; S3 -> SQS in Phase 3)

1. Documents come from the synthetic corpus (`synthetic-data/documents/`).
2. Paragraph-aware chunking with overlap (config: max chars, overlap).
3. Each chunk is embedded and upserted into `document_chunks` (unique on
   source + chunk index; re-ingestion replaces the document atomically).
