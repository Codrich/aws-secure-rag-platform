# Rollback Runbook

**Status: Phase 2+ (no cloud deployments yet).**

## Application rollback

ECS blue/green keeps the previous task set warm during deploy; a failed
health check rolls back automatically. Manual rollback: redeploy the
previous image tag (images are immutable and Cosign-signed).

## Infrastructure rollback

Revert the Terraform commit and re-apply through the pipeline. Never apply
manual console changes; drift is treated as an incident.

## Data rollback

RDS point-in-time restore. Vector data is derived: re-run ingestion from the
source corpus after restore if embeddings and documents diverge.
