variable "project_name" {
  type = string
    default = "aws_resume_analyzer"
}
variable "environment" {
  type = string
  default = "development"
}
variable "lambda_function_name" {
    type = string
    
}
variable "s3_bucket_arn" {
    type = string
   
}
variable "dynamodb_table_arn" {
    type = string
    
}