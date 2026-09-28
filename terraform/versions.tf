terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "devops-circle-terraform-state-868987408509"
    key            = "devops-circle/lab/terraform.tfstate"
    region         = "eu-north-1"
    encrypt        = true
    dynamodb_table = "devops-circle-tf-lock"
  }
}
