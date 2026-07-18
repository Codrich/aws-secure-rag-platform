# Security Policy

## Scope

This is a portfolio reference implementation using synthetic data only. No production data, PHI, or real credentials are present in this repository or its deployed environments.

## Principles

- Least-privilege IAM for every component, scoped to specific actions and resources
- No long-lived cloud credentials: CI authenticates via GitHub Actions OIDC
- Private networking by default: ECS tasks in private subnets, VPC endpoints for AWS services
- Encryption at rest (KMS) and in transit (TLS) for all data stores
- Secrets in AWS Secrets Manager; never in code, config files, or environment defaults
- Redacted logging by default: prompts and model responses are not logged outside a clearly labeled synthetic-data development mode
- Defense in depth for AI-specific risks: Bedrock Guardrails plus independent prompt-injection, retrieval-poisoning, and data-exfiltration test suites (Guardrails are not treated as sufficient alone)

## Reporting

If you find a vulnerability in this reference implementation, please open a GitHub issue or contact the maintainer directly. There is no bug bounty; this is an educational project.
