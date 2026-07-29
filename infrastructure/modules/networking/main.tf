# Network module: VPC with private-by-default posture.
# Phase 2 adds: private/public subnets across 2 AZs, VPC endpoints
# (bedrock-runtime, ecr, logs, secretsmanager, s3), flow logs,
# restrictive security groups, no public IPs on ECS tasks.

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "rag-platform-${var.environment}"
  }
}

resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.this.id

  ingress = []
  egress  = []

  tags = {
    Name        = "rag-platform-${var.environment}-default-sg"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
