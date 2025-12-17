variable "project_name" {
  type        = string
  description = "The name of the project"
}
variable "environment" {
    type        = string
}
variable "api_name" {
    type        = string
}
variable "lambda_function_name" {
    type        = string
}
variable "lambda_invoke_arn" {
    type        = string
}
variable "lambda_upload_function_name" {
    type       = string
}
variable "lambda_upload_invoke_arn" {
  type = string
}