from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)


class GenerateResponse(BaseModel):
    request_id: str
    text: str
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class HealthResponse(BaseModel):
    status: str
    app_env: str
