provider "aws" {
  region = var.region_name
  default_tags {
    tags = {
      Environment = var.environment_name
      Project     = var.project_name
      ManagedBy   = "Terraform"
    }
  }

}