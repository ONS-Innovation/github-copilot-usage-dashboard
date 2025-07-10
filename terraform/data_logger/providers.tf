terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.2.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      "Project"       = var.project_tag
      "TeamOwner"     = var.team_owner_tag
      "BusinessOwner" = var.business_owner_tag
      "Service"       = "${var.project_tag}-copilot-usage-lambda"
      "Environment"   = var.env_name
      "Terraform"     = "true"
    }
  }
}