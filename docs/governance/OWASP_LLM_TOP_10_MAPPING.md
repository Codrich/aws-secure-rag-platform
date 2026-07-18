# OWASP Top 10 for LLM Applications — Control Mapping

Alignment exercise against the OWASP Top 10 for LLM Applications.
Status reflects the phase in which each control lands.

| ID | Risk | Platform controls | Phase |
|----|------|-------------------|-------|
| LLM01 | Prompt Injection | Guardrails prompt-attack detection; input validation; independent direct/indirect injection test suite; retrieved content never treated as instructions | 5 |
| LLM02 | Insecure Output Handling | Output schema validation; no model output executed or rendered as code; size limits | 4 |
| LLM03 | Training Data Poisoning | N/A — no training or fine-tuning; ingestion content validation addresses retrieval poisoning | 3 |
| LLM04 | Model Denial of Service | Token limits; per-identity rate limiting; cost budgets and alarms | 4-7 |
| LLM05 | Supply Chain Vulnerabilities | SCA, container scanning, SBOM (CycloneDX), Cosign image signing, pinned dependencies | 6 |
| LLM06 | Sensitive Information Disclosure | PII masking via Guardrails; redacted logging by default; synthetic data only; document-level authorization | 4-5 |
| LLM07 | Insecure Plugin Design | N/A — no plugins or tool execution in v1; noted for any future agent extension | — |
| LLM08 | Excessive Agency | Model has no tools, no write access, no autonomous actions; generation only | By design |
| LLM09 | Overreliance | Citations required; groundedness checks; refusal-correctness eval cases; hallucination measurement | 6 |
| LLM10 | Model Theft | Bedrock managed service — no model weights held; invocation rights scoped by IAM to specific model ARN | 2 |
