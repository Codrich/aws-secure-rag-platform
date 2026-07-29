# Security Control Traceability

Every row links a risk to the code that mitigates it and the test that
proves it. Rows are added only when implementation and verification exist -
planned controls live in the threat model and FAILURE_MODES.md, not here.

| Risk | Control | Implementation | Verification | Evidence |
|---|---|---|---|---|
| Prompt injection (question or poisoned chunk) | Hardened system prompt; retrieved content confined to user role | `app/rag/prompting.py` | `evaluations/tests/test_prompt_injection.py` | CI run |
| Ungrounded answers / hallucination | No-context deterministic refusal without model call | `app/rag/service.py` | `evaluations/tests/test_groundedness.py` | CI run + scorecard |
| Fabricated citations | Citations derived only from retrieved chunks with real scores | `app/rag/service.py` | `evaluations/tests/test_response_quality.py` | CI run |
| Oversized input (cost/DoS) | Character limits before model invocation | `app/clients/bedrock.py`, `app/models/requests.py` | `app/tests/test_bedrock.py` | CI run |
| Hidden control characters | Input sanitization at API boundary | `app/core/security.py`, `app/api/routes/query.py` | `app/tests/test_security.py`, `app/tests/test_failure_modes.py` | CI run |
| Ungrounded fallback on store outage | Fail-closed 503; model never called | `app/api/routes/query.py` | `app/tests/test_failure_modes.py` | CI run |
| SQL injection via vectors | Parameterized queries; server-side vector cast | `app/rag/retrieval.py` | code review; no string-built SQL | repo |
| Committed secrets | TruffleHog scan on every push/PR | `.github/workflows/security.yml` | workflow run | Actions log |
| IaC misconfiguration | Checkov scan, `soft_fail: false` | `.github/workflows/security.yml` | workflow run | Actions log |
| Prompt/response data leakage via logs | Metadata-only structured logging by default | `app/core/logging.py` | `LOG_FULL_CONTENT` gate, code review | repo |
