# ECS Fargate service module (Phase 2)

Will provision: cluster, task definition (non-root container, read-only root
filesystem), service in private subnets with no public IP, ALB with HTTPS,
task role scoped to bedrock:InvokeModel on the configured model ARN only,
autoscaling, and CloudWatch log group with KMS encryption.
