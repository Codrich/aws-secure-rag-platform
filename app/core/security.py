"""Input-hardening helpers.

First-line request checks that run before any model call. These complement
- never replace - Bedrock Guardrails (Phase 5) and the prompt-injection
evaluation suite in evaluations/security/.
"""
import re

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(text: str) -> str:
    """Strip control characters that can hide instructions from log review."""
    return CONTROL_CHARS.sub("", text)


def exceeds_limit(text: str, max_chars: int) -> bool:
    return len(text) > max_chars
