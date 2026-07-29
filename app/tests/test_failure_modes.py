"""Failure-mode contract tests (docs/security/FAILURE_MODES.md).

Fail-closed behavior must be enforced by code, not documentation.
"""
from unittest.mock import MagicMock

import psycopg
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from app.api.dependencies import get_rag_service
from app.clients.bedrock import BedrockService
from app.main import app
from app.rag.service import RagService

client = TestClient(app)


def make_service(
    store_error: Exception | None = None, bedrock_error: Exception | None = None
) -> tuple[RagService, MagicMock]:
    from app.rag.retrieval import RetrievedChunk

    embeddings = MagicMock()
    embeddings.embed.return_value = [0.1]
    store = MagicMock()
    if store_error is not None:
        store.search.side_effect = store_error
    else:
        store.search.return_value = [
            RetrievedChunk(source="doc.md", chunk_index=0, content="Fact.", score=0.9)
        ]
    bedrock_client = MagicMock()
    if bedrock_error is not None:
        bedrock_client.converse.side_effect = bedrock_error
    else:
        bedrock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": "ok"}]}},
            "usage": {"inputTokens": 1, "outputTokens": 1},
        }
    service = RagService(
        bedrock=BedrockService(client=bedrock_client),
        embeddings=embeddings,
        store=store,
    )
    return service, bedrock_client


def test_vector_store_down_fails_closed_without_model_call() -> None:
    service, bedrock_client = make_service(store_error=psycopg.OperationalError("db down"))
    app.dependency_overrides[get_rag_service] = lambda: service
    try:
        response = client.post("/v1/query", json={"question": "anything"})
    finally:
        app.dependency_overrides.pop(get_rag_service)
    assert response.status_code == 503
    assert "fail-closed" in response.json()["detail"]
    bedrock_client.converse.assert_not_called()


def test_bedrock_throttling_returns_controlled_503() -> None:
    error = ClientError(
        {"Error": {"Code": "ThrottlingException", "Message": "rate exceeded"}}, "Converse"
    )
    service, _ = make_service(bedrock_error=error)
    app.dependency_overrides[get_rag_service] = lambda: service
    try:
        response = client.post("/v1/query", json={"question": "anything"})
    finally:
        app.dependency_overrides.pop(get_rag_service)
    assert response.status_code == 503
    assert response.headers.get("retry-after") == "5"


def test_control_characters_stripped_before_processing() -> None:
    service, bedrock_client = make_service()
    app.dependency_overrides[get_rag_service] = lambda: service
    try:
        response = client.post("/v1/query", json={"question": "what is\x00 the policy\x1b?"})
    finally:
        app.dependency_overrides.pop(get_rag_service)
    assert response.status_code == 200
    sent_prompt = bedrock_client.converse.call_args.kwargs["messages"][0]["content"][0]["text"]
    assert "\x00" not in sent_prompt
    assert "\x1b" not in sent_prompt
