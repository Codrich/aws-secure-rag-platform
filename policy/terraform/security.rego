package main

import rego.v1

resource_changes := input.resource_changes

deny contains violation if {
  resource := resource_changes[_]
  resource.type == "aws_ecs_service"
  resource.change.actions != ["delete"]
  resource.change.after.network_configuration[_].assign_public_ip == true

  violation := {
    "msg": sprintf("%s must not assign public IP addresses to ECS tasks", [resource.address]),
    "control": "NET-001",
    "resource": resource.address,
  }
}

deny contains violation if {
  resource := resource_changes[_]
  resource.type == "aws_db_instance"
  resource.change.actions != ["delete"]
  resource.change.after.publicly_accessible == true

  violation := {
    "msg": sprintf("%s must not expose an RDS instance publicly", [resource.address]),
    "control": "DB-001",
    "resource": resource.address,
  }
}

deny contains violation if {
  resource := resource_changes[_]
  resource.type == "aws_security_group"
  resource.change.actions != ["delete"]

  ingress := resource.change.after.ingress[_]
  cidr := ingress.cidr_blocks[_]
  cidr == "0.0.0.0/0"

  violation := {
    "msg": sprintf("%s must not allow unrestricted IPv4 ingress", [resource.address]),
    "control": "NET-002",
    "resource": resource.address,
  }
}

deny contains violation if {
  resource := resource_changes[_]
  resource.type == "aws_security_group"
  resource.change.actions != ["delete"]

  ingress := resource.change.after.ingress[_]
  cidr := ingress.ipv6_cidr_blocks[_]
  cidr == "::/0"

  violation := {
    "msg": sprintf("%s must not allow unrestricted IPv6 ingress", [resource.address]),
    "control": "NET-003",
    "resource": resource.address,
  }
}