# Auth module (Phase 2)

Cognito JWT validation middleware lands here in Phase 2:

- JWKS fetch and caching from the Cognito user pool
- Signature, issuer, audience, and expiry validation
- Role extraction (user / administrator) for RBAC
- Per-identity rate limiting hooks
