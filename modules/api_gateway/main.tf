resource "aws_apigatewayv2_api" "main" {
    name = var.api_name
    protocol_type = "HTTP"
    description = "AWS API Gateway for Resume Matcher"

    cors_configuration {
        max_age = 300
        allow_headers = ["*"]
        allow_methods = ["GET", "POST", "PUT", "DELETE"]
        allow_origins = ["*"]
    }
    tags ={
        Name = "${var.api_name}-matcher"
    }
}

resource "aws_apigatewayv2_integration" "main" {
    api_id = aws_apigatewayv2_api.main.id
    integration_type = "AWS_PROXY"
    integration_uri = var.lambda_invoke_arn
    integration_method = "POST"
    payload_format_version = "2.0"
    timeout_milliseconds = 30000
}

resource "aws_apigatewayv2_route" "main"{
    api_id = aws_apigatewayv2_api.main.id
    route_key = "POST /match"
    target = "integrations/${aws_apigatewayv2_integration.main.id}"
}

resource "aws_apigatewayv2_stage" "main" {
    api_id = aws_apigatewayv2_api.main.id
    name = "$default"
    auto_deploy = true

    access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
  tags = {
    Name = "${var.project_name}-api-stage"
  }
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.api_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-api-logs"
  }
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Add after existing integration

# Integration with Upload Lambda
resource "aws_apigatewayv2_integration" "upload_integration" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.lambda_upload_invoke_arn
  
  integration_method        = "POST"
  payload_format_version    = "2.0"
  timeout_milliseconds      = 30000  # 60 seconds for upload
}

# Route: POST /upload
resource "aws_apigatewayv2_route" "upload_route" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /upload"
  target    = "integrations/${aws_apigatewayv2_integration.upload_integration.id}"
}

# Lambda permission for upload function
resource "aws_lambda_permission" "api_gateway_invoke_upload" {
  statement_id  = "AllowAPIGatewayInvokeUpload"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_upload_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}