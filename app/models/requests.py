from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """A user question answered from the controlled knowledge base."""

    question: str = Field(min_length=1, max_length=8000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class GenerateRequest(BaseModel):
    """Direct model invocation (dev/diagnostic use; will be gated by RBAC in Phase 4)."""

    prompt: str = Field(min_length=1, max_length=8000)


class IngestRequest(BaseModel):
    """Request to ingest a document already present in the synthetic corpus."""

    source: str = Field(min_length=1, max_length=512)
