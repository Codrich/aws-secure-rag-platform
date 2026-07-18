"""Application settings.

Model ID is configuration, not code: the service works with any Bedrock
text model that supports the Converse API, demonstrating model portability.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-sonnet-example-model-id"
    log_level: str = "INFO"
    # Full prompt/response logging is only permitted in dev with synthetic data.
    log_full_content: bool = False
    max_input_chars: int = 8000
    max_output_tokens: int = 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
