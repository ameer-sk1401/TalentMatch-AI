resource "aws_iam_role" "lambda_role"{
    name = "${var.lambda_function_name}-lambda-role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Action = "sts:AssumeRole",
                Effect = "Allow",
                Principal = {
                    Service = "lambda.amazonaws.com"
                }
            }
        ]
    })
 tags = {
    Name = "${var.project_name}-lambda-role"
 }
}
resource "aws_iam_role_policy_attachment" "lambda-policy-attachment" {
    role =aws_iam_role.lambda_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom_policy" {
    name = "${var.lambda_function_name}-lambda-policy-${var.environment}"
    role = aws_iam_role.lambda_role.name
    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Action = [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                Effect = "Allow",
                Resource = [var.s3_bucket_arn,"${var.s3_bucket_arn}/*"]
            },
            {
                Effect = "Allow"
                Action = [
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem"
                ]
                Resource = [var.dynamodb_table_arn,"${var.dynamodb_table_arn}/index/*"]
            },
            {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        ]
      }
        ]
    })
}