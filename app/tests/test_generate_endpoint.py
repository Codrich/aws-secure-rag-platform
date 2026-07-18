from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.main import app, get_bedrock_service
from app.bedrock.client import BedrockService

client = TestClient(app)


def override_service() -> BedrockService:
    mock = MagicMock()
    mock.converse.return_value = {
        "output": {"message": {"content": [{"text": "synthetic answer"}]}},
        "usage": {"inputTokens": 8, "outputTokens": 4},
    }
    return BedrockService(client=mock)


app.dependency_overrides[get_bedrock_service] = override_service


def test_generate_returns_response() -> None:
    response = client.post("/v1/generate", json={"prompt": "What layers exist?"})
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "synthetic answer"
    assert body["input_tokens"] == 8


def test_generate_rejects_empty_prompt() -> None:
    response = client.post("/v1/generate", json={"prompt": ""})
    assert response.status_code == 422
