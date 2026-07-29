from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.dependencies import get_bedrock_service, get_rag_service
from app.clients.bedrock import BedrockService
from app.main import app
from app.rag.service import NO_CONTEXT_ANSWER, RagService

client = TestClient(app)


def make_bedrock(text: str = "grounded answer [1]") -> BedrockService:
    mock = MagicMock()
    mock.converse.return_value = {
        "output": {"message": {"content": [{"text": text}]}},
        "usage": {"inputTokens": 8, "outputTokens": 4},
    }
    return BedrockService(client=mock)


def make_rag(chunks: list[object] | None = None) -> RagService:
    from app.rag.retrieval import RetrievedChunk

    embeddings = MagicMock()
    embeddings.embed.return_value = [0.1, 0.2]
    store = MagicMock()
    store.search.return_value = chunks if chunks is not None else [
        RetrievedChunk(
            source="policy.md", chunk_index=0, content="Retention is 7 years.", score=0.9
        )
    ]
    return RagService(bedrock=make_bedrock(), embeddings=embeddings, store=store)


def test_query_returns_answer_with_citations() -> None:
    app.dependency_overrides[get_rag_service] = lambda: make_rag()
    try:
        response = client.post("/v1/query", json={"question": "What is the retention period?"})
    finally:
        app.dependency_overrides.pop(get_rag_service)
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "grounded answer [1]"
    assert body["citations"][0]["source"] == "policy.md"


def test_query_refuses_without_context() -> None:
    app.dependency_overrides[get_rag_service] = lambda: make_rag(chunks=[])
    try:
        response = client.post("/v1/query", json={"question": "What was Q3 revenue?"})
    finally:
        app.dependency_overrides.pop(get_rag_service)
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == NO_CONTEXT_ANSWER
    assert body["citations"] == []


def test_generate_returns_response() -> None:
    app.dependency_overrides[get_bedrock_service] = lambda: make_bedrock("synthetic answer")
    try:
        response = client.post("/v1/generate", json={"prompt": "What layers exist?"})
    finally:
        app.dependency_overrides.pop(get_bedrock_service)
    assert response.status_code == 200
    assert response.json()["text"] == "synthetic answer"


def test_generate_rejects_empty_prompt() -> None:
    response = client.post("/v1/generate", json={"prompt": ""})
    assert response.status_code == 422
