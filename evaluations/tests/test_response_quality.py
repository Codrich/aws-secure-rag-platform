"""Response-quality gates that run offline.

Citations must map one-to-one to retrieved chunks and carry real scores.
Phase 5 adds model-graded relevance and completeness scoring.
"""
from unittest.mock import MagicMock

from app.clients.bedrock import BedrockService
from app.rag.retrieval import RetrievedChunk
from app.auth.permissions import Role, allowed_classifications
from app.auth.tenancy import TenantContext
from app.rag.service import RagService


def test_citations_match_retrieved_chunks() -> None:
    chunks = [
        RetrievedChunk(source="a.md", chunk_index=0, content="A", score=0.91),
        RetrievedChunk(source="b.md", chunk_index=2, content="B", score=0.72),
    ]
    mock = MagicMock()
    mock.converse.return_value = {
        "output": {"message": {"content": [{"text": "Answer [1][2]"}]}},
        "usage": {"inputTokens": 5, "outputTokens": 3},
    }
    embeddings = MagicMock()
    embeddings.embed.return_value = [0.1]
    store = MagicMock()
    store.search.return_value = chunks
    result = RagService(
        bedrock=BedrockService(client=mock), embeddings=embeddings, store=store
    ).query("q", context=TenantContext(
        tenant_id="tenant-a",
        role=Role.READER,
        allowed_classifications=allowed_classifications(Role.READER),
    ))
    assert [c.source for c in result.citations] == ["a.md", "b.md"]
    assert all(0.0 <= c.score <= 1.0 for c in result.citations)
