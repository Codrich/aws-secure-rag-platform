"""FastAPI application.

Phase 1: health endpoint and a Bedrock generate endpoint.
Phase 2+: Cognito JWT auth middleware, retrieval, guardrails, rate limiting.
"""
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from app.api.schemas import GenerateRequest, GenerateResponse, HealthResponse
from app.bedrock.client import BedrockService, PromptTooLargeError
from app.config.logging import configure_logging
from app.config.settings import Settings, get_settings

configure_logging()

app = FastAPI(
    title="AWS Secure RAG Platform",
    description="Security-first RAG service on Amazon Bedrock (Phase 1)",
    version="0.1.0",
)


def get_bedrock_service() -> BedrockService:
    return BedrockService()


@app.get("/healthz", response_model=HealthResponse)
def healthz(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(status="ok", app_env=settings.app_env)


@app.post("/v1/generate", response_model=GenerateResponse)
def generate(
    body: GenerateRequest,
    service: Annotated[BedrockService, Depends(get_bedrock_service)],
) -> GenerateResponse:
    try:
        result = service.invoke(body.prompt)
    except PromptTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    return GenerateResponse(**result.__dict__)
