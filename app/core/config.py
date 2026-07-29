"""Application settings.

Model IDs are configuration, not code: the service works with any Bedrock
text model that supports the Converse API and any Bedrock embedding model,
demonstrating model portability.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-sonnet-example-model-id"
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    embedding_dimensions: int = 1024
    log_level: str = "INFO"
    # Full prompt/response logging is only permitted in dev with synthetic data.
    log_full_content: bool = False
    max_input_chars: int = 8000
    max_output_tokens: int = 1024

    # Vector store (local dev defaults; production values come from Secrets Manager)
    database_url: str = "postgresql://rag:rag@localhost:5432/rag"
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.35

    # Chunking
    chunk_max_chars: int = 1200
    chunk_overlap_chars: int = 150

    # Tenancy (dev resolver only; replaced by verified Cognito claims in M4)
    tenant_allowlist: str = "tenant-a,tenant-b"
    default_tenant_role: str = "reader"

    @property
    def tenant_allowlist_values(self) -> frozenset[str]:
        return frozenset(t.strip() for t in self.tenant_allowlist.split(",") if t.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
