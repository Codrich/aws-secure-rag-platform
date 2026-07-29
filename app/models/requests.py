from pydantic import BaseModel, ConfigDict, Field

from app.auth.permissions import Classification


class QueryRequest(BaseModel):
    """A user question answered from the controlled knowledge base.

    Tenant identity is deliberately absent: it is resolved server-side and
    can never be asserted by the caller. Unknown fields are rejected so a
    smuggled `tenant_id` fails loudly instead of being silently ignored.
    """

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=8000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class GenerateRequest(BaseModel):
    """Direct model invocation. Admin-only: it bypasses retrieval entirely."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1, max_length=8000)


class IngestRequest(BaseModel):
    """Ingest a document from the synthetic corpus into the caller's tenant."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, max_length=512)
    classification: Classification
