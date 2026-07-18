# RDS PostgreSQL + pgvector module (Phase 2)

Will provision: RDS PostgreSQL in private subnets, pgvector extension,
KMS-encrypted storage, automated backups, Secrets Manager-managed
credentials with rotation, and a security group admitting only the ECS
service. ADR: chosen over OpenSearch Serverless for v1 to avoid the
always-on OCU cost floor; see docs/architecture/.
