# ECS Fargate service module (Phase 2).
# Planned resources: cluster, task definition (no public IP, private subnets),
# service behind an internal ALB, task role scoped to bedrock:InvokeModel on
# the configured model ARN only, log group with KMS encryption.
