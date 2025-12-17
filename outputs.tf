output "region_name" {
  value = var.region_name
}
output "bucket_name" {
  value = module.s3_bucket.bucket_id
}
output "bucket_arn" {
  value = module.s3_bucket.bucket_arn
}
output "dynamodb_table_name" {
  value = module.dynamodb_table.table_name
}
output "table_arn" {
  value = module.dynamodb_table.table_arn
}
output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.iam.lambda_role_arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda_matcher.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.lambda_matcher.function_arn
}
output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "api_invoke_url" {
  description = "Full API invoke URL"
  value       = module.api_gateway.invoke_url
}
output "lambda_uploader_name" {
  description = "Name of the Lambda uploader function"
  value       = module.lambda_uploader.function_name
}
output "lambda_uploader_arn" {
    description = "ARN of the Lambda uploader function"
    value       = module.lambda_uploader.function_arn
}