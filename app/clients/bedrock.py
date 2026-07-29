"""Amazon Bedrock invocation service.

Wraps the Converse API with input validation, size limits, timing,
and redacted structured logging. Model ID comes from configuration.
"""
import time
import uuid
from dataclasses import dataclass
from typing import Any

import boto3

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptTooLargeError(ValueError):
    """Input exceeds the configured character limit."""


@dataclass(frozen=True)
class InvocationResult:
    request_id: str
    text: str
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class BedrockService:
    def __init__(self, client: Any | None = None) -> None:
        settings = get_settings()
        self._settings = settings
        self._client = client or boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def invoke(self, prompt: str, system: str | None = None) -> InvocationResult:
        settings = self._settings
        if len(prompt) > settings.max_input_chars:
            raise PromptTooLargeError(
                f"Input of {len(prompt)} chars exceeds limit of {settings.max_input_chars}"
            )

        request_id = str(uuid.uuid4())
        start = time.monotonic()

        kwargs: dict[str, Any] = {
            "modelId": settings.bedrock_model_id,
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": settings.max_output_tokens},
        }
        if system:
            kwargs["system"] = [{"text": system}]

        response = self._client.converse(**kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)

        usage = response.get("usage", {})
        text = "".join(
            block.get("text", "")
            for block in response.get("output", {}).get("message", {}).get("content", [])
        )

        result = InvocationResult(
            request_id=request_id,
            text=text,
            model_id=settings.bedrock_model_id,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            latency_ms=latency_ms,
        )

        log = logger.bind(
            request_id=request_id,
            model_id=result.model_id,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            latency_ms=latency_ms,
        )
        if settings.log_full_content and settings.app_env == "dev":
            log = log.bind(prompt=prompt, response=text, synthetic_data_mode=True)
        log.info("bedrock_invocation")

        return result
