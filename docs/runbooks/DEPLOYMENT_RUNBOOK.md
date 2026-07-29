# Deployment Runbook

**Status: Phase 2+ (no cloud deployments yet).** Local development uses
`make dev`.

## Planned production flow

1. PR merged to `main` with green CI (lint, types, tests, IaC scan, secrets scan).
2. Image built, Trivy-scanned, SBOM generated (CycloneDX), Cosign-signed, pushed to ECR.
3. Terraform plan posted to the PR; apply via OIDC-authenticated workflow after approval.
4. ECS blue/green deploy; health checks gate traffic shift.
5. Post-deploy: smoke test `POST /v1/query` against the golden dataset subset.

## Verification checklist

- `/healthz` returns 200 in the new task set
- CloudWatch dashboard shows traffic on the new deployment
- No guardrail-intervention or 5xx alarm firing
