"""Structured JSON logging with redaction-by-default.

Prompts and model responses are never logged unless LOG_FULL_CONTENT=true,
which is only permitted in dev mode with synthetic data. Production logs
carry metadata only: request IDs, token counts, latency, model ID.
"""
import logging
from typing import cast

import structlog

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return cast(structlog.BoundLogger, structlog.get_logger(name))
