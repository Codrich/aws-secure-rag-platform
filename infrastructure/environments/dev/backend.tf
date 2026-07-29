# Phase 2: remote state before the first real apply.
# Bucket is versioned, encrypted (SSE-KMS), and locked via DynamoDB.
#
# terraform {
#   backend "s3" {
#     bucket         = "rag-platform-tfstate-<account-id>"
#     key            = "dev/terraform.tfstate"
#     region         = "us-east-1"
#     dynamodb_table = "rag-platform-tf-locks"
#     encrypt        = true
#   }
# }
