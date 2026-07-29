# Cloud Operations Guide (Synthetic)

> Entirely synthetic document for platform testing.

## Environments

The platform runs dev, staging, and production environments in separate AWS
accounts. Production changes require a peer-reviewed pull request and a green
pipeline.

## Deployments

Deployments are blue/green through ECS. A failed health check triggers
automatic rollback to the previous task set within 5 minutes.

## Backups

RDS snapshots are taken nightly and retained for 35 days. Restore drills run
quarterly.
