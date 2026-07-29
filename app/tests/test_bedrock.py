from unittest.mock import MagicMock

import pytest

from app.clients.bedrock import BedrockService, PromptTooLargeError


def make_mock_client(text: str = "hello") -> MagicMock:
    mock = MagicMock()
    mock.converse.return_value = {
        "output": {"message": {"content": [{"text": text}]}},
        "usage": {"inputTokens": 10, "outputTokens": 5},
    }
    return mock


def test_invoke_returns_text_and_usage() -> None:
    service = BedrockService(client=make_mock_client("grounded answer"))
    result = service.invoke("What is the retention policy?")
    assert result.text == "grounded answer"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.request_id


def test_invoke_rejects_oversized_input() -> None:
    service = BedrockService(client=make_mock_client())
    with pytest.raises(PromptTooLargeError):
        service.invoke("x" * 100_000)


def test_invoke_passes_model_id_from_config() -> None:
    mock = make_mock_client()
    service = BedrockService(client=mock)
    service.invoke("hi")
    assert "modelId" in mock.converse.call_args.kwargs
