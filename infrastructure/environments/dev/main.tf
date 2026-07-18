terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Phase 2: S3 backend with DynamoDB locking
  # backend "s3" {}
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "aws-secure-rag-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "network" {
  source      = "../../modules/network"
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
}

# Phase 2:
# module "rds_pgvector" { source = "../../modules/rds_pgvector" ... }
# module "ecs_service"  { source = "../../modules/ecs_service" ... }
