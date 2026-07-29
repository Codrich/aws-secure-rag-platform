# Failure-Mode Contract

Required behavior under failure. Each implemented row is enforced by a test;
rows marked Planned land with the milestone shown and must arrive with tests.

| Failure | Required behavior | Status | Verification |
|---|---|---|---|
| Vector store unavailable | 503, refuse; never call the model | Implemented | `app/tests/test_failure_modes.py` |
| No qualifying chunks | Deterministic refusal; no model call, no model memory | Implemented | `evaluations/tests/test_groundedness.py` |
| Bedrock throttled | Controlled 503 with `Retry-After` | Implemented | `app/tests/test_failure_modes.py` |
| Oversized input | 413 before any model call | Implemented | `app/tests/test_bedrock.py`, `app/tests/test_query.py` |
| Control characters in input | Stripped before processing | Implemented | `app/tests/test_failure_modes.py` |
| Tenant context missing | 401/403 | Planned (M2) | with tenancy implementation |
| Invalid document classification | Reject ingestion | Planned (M2) | with tenancy implementation |
| Duplicate ingestion event | Idempotent processing | Planned (M6) | with SQS pipeline |
| Guardrail layer error | **Profile-dependent**: `prod` fails closed; `dev`/`test` degrade with an explicit warning and structured log event | Planned (stretch, Guardrails integration) | with Guardrails integration |
