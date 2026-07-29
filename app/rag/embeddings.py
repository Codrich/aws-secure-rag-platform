"""Bedrock embedding client.

Uses the configured embedding model (Titan Text Embeddings v2 by default).
The client is injectable for testing; no network calls in unit tests.
"""
import json
from typing import Any

import boto3

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self, client: Any | None = None) -> None:
        settings = get_settings()
        self._settings = settings
        self._client = client or boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def embed(self, text: str) -> list[float]:
        body = json.dumps(
            {"inputText": text, "dimensions": self._settings.embedding_dimensions}
        )
        response = self._client.invoke_model(
            modelId=self._settings.embedding_model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
        embedding: list[float] = payload["embedding"]
        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]
