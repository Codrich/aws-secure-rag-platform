# AWS Secure RAG Platform

> Production-style, security-first Retrieval-Augmented Generation platform on AWS Bedrock — built with Terraform, ECS Fargate, FastAPI, and a DevSecOps pipeline with AI evaluation gates.

**Status: Phase 1 — Core service and infrastructure skeleton.** See [Roadmap](#roadmap).

## Overview

This project implements a secure RAG platform that lets authenticated users query a controlled knowledge base and receive grounded, cited answers from an Amazon Bedrock foundation model — with guardrails, private networking, AI evaluation gates in CI, and governance documentation aligned with the NIST AI RMF and OWASP Top 10 for LLM Applications.

It is a platform-engineering and AI-security project, not a chatbot demo. All data is synthetic. Compliance mappings are alignment exercises, not certifications.

## Architecture (target)

```
User
  |
Amazon API Gateway  (WAF, rate limiting)
  |
Amazon Cognito  (OAuth 2.0 / JWT, RBAC)
  |
FastAPI RAG Service on ECS Fargate  (private subnets, no public IPs)
  |
  +-- Amazon Bedrock (configurable model ID) + Bedrock Guardrails
  +-- PostgreSQL + pgvector  (vector store, encrypted, private)
  +-- Amazon S3  (synthetic document store)
  +-- DynamoDB  (request metadata)
  +-- SQS  (ingestion jobs, DLQ)
  +-- KMS + Secrets Manager
  |
CloudWatch + CloudTrail  (redacted, structured logs; token/cost metrics)
```

### Architecture decision: pgvector vs. OpenSearch Serverless

v1 uses PostgreSQL with pgvector as the vector store. It demonstrates the same RAG capabilities (embeddings, similarity search, metadata filtering, private connectivity, encryption, backups) without the always-on OCU cost floor of OpenSearch Serverless. For larger-scale enterprise workloads — high ingest throughput, hybrid lexical+vector search, Bedrock Knowledge Base native integration — OpenSearch Serverless is the recommended alternative and is documented as such in `docs/architecture/`.

## Security posture (target)

- Least-privilege IAM scoped to specific model invocations
- Private subnets, VPC endpoints, no public IPs on tasks
- Bedrock Guardrails: prompt-attack detection, PII masking, contextual grounding
- Own prompt-injection test suite (Guardrails are not treated as complete protection)
- Redacted logging by default: no full prompts/responses outside labeled synthetic-data dev mode
- Signed container images (Cosign), SBOM (CycloneDX), IaC scanning (Checkov)
- Governance: `docs/governance/` — threat model, NIST AI RMF and OWASP LLM Top 10 mappings

## Quickstart (local development)

```bash
# Requires Docker and AWS credentials with bedrock:InvokeModel
cp .env.example .env   # set BEDROCK_MODEL_ID and AWS_REGION
make dev               # build and run with docker-compose
curl localhost:8000/healthz
```

Run checks:

```bash
make lint   # ruff + mypy
make test   # pytest
```

## Repository structure

```
app/            FastAPI service (api, bedrock client, auth, config, tests)
infrastructure/ Terraform modules and dev environment
evaluations/    Golden datasets and AI security test cases (CI gates)
policies/       Policy-as-code (OPA/Conftest), IAM baselines
observability/  CloudWatch dashboards and alarms
docs/           Architecture, governance, runbooks
```

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | FastAPI + Bedrock invocation, Docker, tests, Terraform skeleton, CI validation, governance docs | In progress |
| 2 | AWS foundation: VPC, ECS Fargate, RDS pgvector, Cognito, KMS, Secrets Manager | Planned |
| 3 | Ingestion pipeline: S3 -> SQS -> chunking -> embeddings -> pgvector (DLQ, status tracking) | Planned |
| 4 | Authenticated RAG API: retrieval, citations, document-level authorization, rate limiting | Planned |
| 5 | AI security: Bedrock Guardrails, prompt-injection test suite, PII controls | Planned |
| 6 | DevSecOps: full pipeline with SBOM, Cosign signing, policy gates, eval gates | Planned |
| 7 | Observability: token/cost dashboards, guardrail intervention metrics, alarms | Planned |
| 8 | Optional: EKS deployment variant (Helm, ArgoCD), OpenSearch Serverless variant | Future |

## Governance documentation

- [Threat model](docs/governance/THREAT_MODEL.md)
- [NIST AI RMF mapping](docs/governance/NIST_AI_RMF_MAPPING.md)
- [OWASP LLM Top 10 mapping](docs/governance/OWASP_LLM_TOP_10_MAPPING.md)
- [AI incident response runbook](docs/runbooks/AI_INCIDENT_RESPONSE_RUNBOOK.md)
- [Security policy](SECURITY.md)

## License

MIT
