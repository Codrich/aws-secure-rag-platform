# AI security test suite (Phase 5)

Independent tests beyond Bedrock Guardrails:

- Indirect prompt injection embedded in uploaded synthetic documents
- System-prompt disclosure attempts
- Retrieval poisoning (malicious content injected at ingestion)
- Unauthorized document access across roles
- Encoded/obfuscated attacks (base64, homoglyphs, split payloads)
- Token-exhaustion and cost-abuse patterns

Each test asserts an expected control response (block, refusal, masking,
authorization denial) and runs as a CI gate: the pipeline fails when a
control regresses.

## Implementation status

The `expected` values in these case files describe the *intended* control.
They do not assert that the control is implemented. Each case carries a
`control_status` field recording what is actually verified today.

### `sensitive_data_cases.json` - `control_status: detection_only`

`evaluations/tests/test_sensitive_data.py` executes all cases against
`app.core.sensitive_data` and verifies **detection behavior only**: the
correct pattern fires for each case, `redact()` removes the matched value,
and ordinary questions are not flagged.

Request/response enforcement is **not implemented**. The detector is not
called from `RagService`, the API routes, or any other runtime path, so:

- no request containing an SSN or credential is blocked at runtime
- no answer containing PII is masked at runtime
- the offline gate makes no claim about live RAG behavior

The scorecard in `scripts/run_evaluations.py` labels this row
"Sensitive-data detection (not enforced)" for that reason. A tripwire test
fails if a case is promoted beyond `detection_only` without enforcement
gates being added, so the suite cannot silently vouch for a control it does
not exercise.

Note that the tripwire is a documentation check, not a code check: nothing
automatically detects enforcement being wired into `RagService`. Whoever
implements Phase 5 enforcement must update `control_status` and the
scorecard label by hand.

Runtime enforcement, layered with Bedrock Guardrails, is Phase 5 work.
