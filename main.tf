module "s3_bucket" {
  source            = "./modules/s3_bucket"
  bucket_name       = "${var.project_name}-resumes-${var.environment_name}-${data.aws_caller_identity.current.account_id}"
  enable_versioning = var.enable_versioning
  force_destroy     = var.force_destroy
}
module "dynamodb_table" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
  environment  = var.environment_name
  table_name   = "${var.project_name}-metadata-${var.environment_name}-${data.aws_caller_identity.current.account_id}"
  billing_mode = "PAY_PER_REQUEST"
}
data "aws_caller_identity" "current" {}

module "iam" {
    source = "./modules/IAM"
    project_name = var.project_name
    environment  = var.environment_name
    lambda_function_name = "${var.project_name}-lambda-${var.environment_name}-${data.aws_caller_identity.current.account_id}"
    s3_bucket_arn = module.s3_bucket.bucket_arn
    dynamodb_table_arn = module.dynamodb_table.table_arn
}


module "lambda_matcher" {
  source = "./modules/lambda"

  project_name        = var.project_name
  environment         = var.environment_name
  function_name       = "${var.project_name}-matcher-${var.environment_name}"
  lambda_role_arn     = module.iam.lambda_role_arn
  s3_bucket_name      = module.s3_bucket.bucket_id
  dynamodb_table_name = module.dynamodb_table.table_name
  telegram_bot_token  = var.telegram_bot_token
  lambda_zip_path     = "${path.root}/lambda_matcher.zip"
}


module "lambda_uploader" {
  source = "./modules/lambda"

  project_name        = var.project_name
  environment         = var.environment_name
  function_name       = "${var.project_name}-uploader-${var.environment_name}"
  lambda_role_arn     = module.iam.lambda_role_arn
  s3_bucket_name      = module.s3_bucket.bucket_id
  dynamodb_table_name = module.dynamodb_table.table_name
  telegram_bot_token  = ""
  lambda_zip_path     = "${path.root}/lambda_uploader.zip"
  timeout             = 30  
  memory_size         = 1024
}


module "api_gateway" {
  source = "./modules/api_gateway"
  project_name                 = var.project_name
  environment                  = var.environment_name
  api_name                     = "${var.project_name}-api-${var.environment_name}"
  lambda_function_name         = module.lambda_matcher.function_name
  lambda_invoke_arn            = module.lambda_matcher.invoke_arn
  lambda_upload_function_name  = module.lambda_uploader.function_name
  lambda_upload_invoke_arn     = module.lambda_uploader.invoke_arn
}

