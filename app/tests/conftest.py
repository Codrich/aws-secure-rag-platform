"""Shared test helpers."""
from unittest.mock import MagicMock

from app.auth.permissions import Classification, Role, allowed_classifications
from app.auth.tenancy import TenantContext
from app.clients.bedrock import BedrockService

TENANT_A_HEADERS = {"X-Tenant-Id": "tenant-a", "X-Tenant-Role": "reader"}
TENANT_B_HEADERS = {"X-Tenant-Id": "tenant-b", "X-Tenant-Role": "reader"}
ADMIN_A_HEADERS = {"X-Tenant-Id": "tenant-a", "X-Tenant-Role": "admin"}


def context(tenant_id: str = "tenant-a", role: Role = Role.READER) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        role=role,
        allowed_classifications=allowed_classifications(role),
    )


def make_bedrock(text: str = "grounded answer [1]") -> BedrockService:
    mock = MagicMock()
    mock.converse.return_value = {
        "output": {"message": {"content": [{"text": text}]}},
        "usage": {"inputTokens": 8, "outputTokens": 4},
    }
    return BedrockService(client=mock)


def chunk(source: str = "policy.md", content: str = "Retention is 7 years.") -> object:
    from app.rag.retrieval import RetrievedChunk

    return RetrievedChunk(source=source, chunk_index=0, content=content, score=0.9)


__all__ = [
    "ADMIN_A_HEADERS",
    "TENANT_A_HEADERS",
    "TENANT_B_HEADERS",
    "Classification",
    "chunk",
    "context",
    "make_bedrock",
]
