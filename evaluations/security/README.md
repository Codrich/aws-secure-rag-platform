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
