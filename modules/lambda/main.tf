# Lambda Function
resource "aws_lambda_function" "main" {
  filename         = var.lambda_zip_path
  function_name    = var.function_name
  role             = var.lambda_role_arn
  handler          = var.handler
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = {
      S3_BUCKET_NAME      = var.s3_bucket_name
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
      ENVIRONMENT         = var.environment
      TELEGRAM_BOT_TOKEN  = var.telegram_bot_token
    }
  }

  tags = {
    Name = var.function_name
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-lambda-logs"
  }
}