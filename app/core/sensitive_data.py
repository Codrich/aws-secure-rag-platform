"""Deterministic sensitive-data detection.

Pattern-based detection of national identifiers, credential-like strings and
email addresses. Detection here is a behavioral property of the patterns
below, not a measured accuracy score.

Enforcement status: this module is a detection library only. It is NOT
called from RagService, the API routes, or any other request/response path,
so the platform does not currently block or mask sensitive data at runtime.
Nothing here changes Milestone 1 or Milestone 2 behavior. Runtime
enforcement, layered with Bedrock Guardrails, is Phase 5 work.
"""
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class SensitiveKind(StrEnum):
    """Category of sensitive value found in a span of text."""

    SSN = "ssn"
    CREDENTIAL = "credential"
    EMAIL = "email"


class Disposition(StrEnum):
    """Control decision that *would* apply if enforcement were wired in.

    This is the detector's recommendation, not an action taken by the
    platform. No caller acts on it today.
    """

    BLOCK = "block"
    MASK = "mask"
    ALLOW = "allow"


SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Credential-like tokens: a recognised prefix, a separator, then at least six
# token characters. Matches synthetic fixtures such as "sk-synthetic-000000".
CREDENTIAL_PATTERN = re.compile(
    r"\b(?:sk|pk|api[-_]?key|token|bearer)[-_][A-Za-z0-9][A-Za-z0-9_-]{5,}\b",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Ordered most-specific first so credentials are redacted before the looser
# email pattern can claim part of the same span.
_PATTERNS: tuple[tuple[SensitiveKind, re.Pattern[str]], ...] = (
    (SensitiveKind.SSN, SSN_PATTERN),
    (SensitiveKind.CREDENTIAL, CREDENTIAL_PATTERN),
    (SensitiveKind.EMAIL, EMAIL_PATTERN),
)

# Kinds that would never be stored or echoed, even masked in place.
BLOCKING_KINDS = frozenset({SensitiveKind.SSN, SensitiveKind.CREDENTIAL})


@dataclass(frozen=True)
class Finding:
    """A single sensitive value located in scanned text."""

    kind: SensitiveKind
    value: str
    start: int
    end: int


def scan(text: str) -> list[Finding]:
    """Return every sensitive value found in ``text``, ordered by position."""
    findings: list[Finding] = []
    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                Finding(kind=kind, value=match.group(0), start=match.start(), end=match.end())
            )
    return sorted(findings, key=lambda finding: finding.start)


def redact(text: str) -> str:
    """Return ``text`` with every sensitive value replaced by a placeholder.

    Pure function. Callers decide what to do with the result; no response
    body is redacted by the platform today.
    """
    redacted = text
    for kind, pattern in _PATTERNS:
        redacted = pattern.sub(f"[REDACTED:{kind.value.upper()}]", redacted)
    return redacted


def disposition(findings: Sequence[Finding]) -> Disposition:
    """Map findings to the control decision that would apply under enforcement.

    Blocking kinds dominate: one credential in an otherwise clean request is
    still a block. Text with no findings is explicitly allowed, so the gate
    cannot be satisfied by a detector that flags everything.
    """
    if not findings:
        return Disposition.ALLOW
    if any(finding.kind in BLOCKING_KINDS for finding in findings):
        return Disposition.BLOCK
    return Disposition.MASK
