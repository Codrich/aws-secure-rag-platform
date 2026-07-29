"""Cognito JWT verification (Phase 2 wiring).

Verifies RS256 tokens against the user pool's JWKS. Not yet mounted as
middleware - it is enabled when the Cognito Terraform module is applied
and COGNITO_* settings are present. Kept import-safe without them.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    username: str
    groups: tuple[str, ...]


class CognitoVerifierNotConfiguredError(RuntimeError):
    """Raised when JWT verification is attempted without Cognito settings."""


def verify_token(token: str) -> AuthenticatedUser:
    """Verify a Cognito access token and return the authenticated user.

    Phase 2 implements JWKS fetch/cache and RS256 signature, expiry,
    issuer, and client-id validation here (python-jose or pyjwt[crypto]).
    """
    raise CognitoVerifierNotConfiguredError(
        "Cognito verification is enabled in Phase 2 when the user pool exists."
    )
