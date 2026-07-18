# Threat Model — AWS Secure RAG Platform

Methodology: STRIDE applied to each trust boundary, extended with
AI-specific threats from OWASP LLM Top 10 and MITRE ATLAS. Synthetic
data only; severity ratings assume a production deployment of the same
architecture.

## System assets

- Foundation model access (Bedrock invocation rights)
- Knowledge base content and embeddings (pgvector, S3)
- User identities and JWTs (Cognito)
- Audit logs and telemetry
- CI/CD pipeline and container images

## Trust boundaries

1. Internet -> API Gateway (WAF)
2. API Gateway -> FastAPI service (Cognito JWT)
3. Service -> Bedrock (IAM, VPC endpoint)
4. Service -> pgvector/S3/DynamoDB (IAM, security groups)
5. Ingestion pipeline -> knowledge base (content validation)
6. GitHub Actions -> AWS (OIDC, short-lived credentials)

## Key threats and mitigations

| # | Threat | Vector | Mitigations |
|---|--------|--------|-------------|
| T1 | Direct prompt injection | User query | Bedrock Guardrails prompt-attack detection; input validation and size limits; independent injection test suite in CI |
| T2 | Indirect prompt injection | Malicious content in ingested documents | Ingestion-time content scanning; retrieval-poisoning tests; instructions in retrieved content never treated as commands |
| T3 | Sensitive data disclosure | Model output leaks PII or system instructions | Guardrails PII masking; output filtering; redacted logging by default |
| T4 | Unauthorized document access | User queries documents beyond their role | Document-level authorization enforced at retrieval, not post-generation; authz test cases in golden dataset |
| T5 | Model cost abuse / token exhaustion | Oversized or repeated requests | Input/output token limits; per-identity rate limiting; cost alarms |
| T6 | Credential theft | Long-lived keys in CI or code | OIDC only; secret scanning (TruffleHog) as pipeline gate; Secrets Manager at runtime |
| T7 | Supply-chain compromise | Malicious dependency or image | SCA; container scanning; SBOM; Cosign-signed images |
| T8 | Data exfiltration via network | Compromised task reaches internet | Private subnets, no public IPs, VPC endpoints, restrictive egress |
| T9 | Hallucinated/ungrounded answers | Model asserts unsupported claims | Contextual-grounding checks; citation requirements; groundedness eval gate |
| T10 | Audit log tampering | Attacker hides activity | CloudTrail; append-only log design; KMS-encrypted log groups |

## Out of scope (v1)

Model training attacks (no training occurs), multi-tenant isolation
(single-tenant v1), DDoS beyond WAF/API Gateway defaults.

Review cadence: revisit at each phase completion.
