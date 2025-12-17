variable "region_name" {
  description = "AWS region name"
  default     = "us-east-1"
}
variable "environment_name" {
  default = "development"
}
variable "project_name" {
  default = "aws-resume-analyzer"
}
variable "enable_versioning" {
  default = true
}
variable "telegram_bot_token" {
  type = string
  sensitive = true
}
variable "force_destroy" {
    type = bool
}