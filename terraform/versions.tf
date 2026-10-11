terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }

  # By default state is kept in a local file (terraform.tfstate, git-ignored).
  # Fine for a course project. For a team, store it remotely instead:
  #
  # backend "s3" {
  #   bucket         = "your-unique-state-bucket"
  #   key            = "quickdesk/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  # Every resource gets these tags, which makes leftovers easy to find in the console.
  default_tags {
    tags = local.tags
  }
}
