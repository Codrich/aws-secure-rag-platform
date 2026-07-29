from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_env: str


class Citation(BaseModel):
    source: str
    chunk_index: int
    score: float


class QueryResponse(BaseModel):
    request_id: str
    answer: str
    citations: list[Citation]
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class GenerateResponse(BaseModel):
    request_id: str
    text: str
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class IngestResponse(BaseModel):
    source: str
    chunks_ingested: int
