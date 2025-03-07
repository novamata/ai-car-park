# --------------------#
# PROVIDER AND REGION #
# --------------------#

provider "aws" {
  region = var.aws_region
}

# -----------------------#
# IAM ROLES AND POLICIES #
# -----------------------#

resource "aws_iam_role" "lambda_role" {
  name = "car_park_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_rekognition" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRekognitionFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_sns" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
}

# -----------------#
# S3 BUCKETS       #
# -----------------#

resource "aws_s3_bucket" "frontend_bucket" {
  bucket = "${var.frontend_bucket_prefix}-${random_string.suffix.result}"
}

resource "aws_s3_bucket_ownership_controls" "frontend_bucket_ownership" {
  bucket = aws_s3_bucket.frontend_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend_bucket_access" {
  bucket = aws_s3_bucket.frontend_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend_bucket_policy" {
  bucket = aws_s3_bucket.frontend_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend_bucket.arn}/*"
      }
    ]
  })
  depends_on = [aws_s3_bucket_public_access_block.frontend_bucket_access]
}

resource "aws_s3_bucket_website_configuration" "frontend_website" {
  bucket = aws_s3_bucket.frontend_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket" "car_images_bucket" {
  bucket = "${var.car_images_bucket_prefix}-${random_string.suffix.result}"
}

resource "aws_s3_object" "uploads_folder" {
  bucket  = aws_s3_bucket.car_images_bucket.id
  key     = "uploads/"
  content = ""  
}

resource "aws_s3_bucket_lifecycle_configuration" "car_images_lifecycle" {
  bucket = aws_s3_bucket.car_images_bucket.id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"
    
    filter {
      prefix = "uploads/"
    }

    transition {
      days          = 7
      storage_class = "GLACIER"
    }
  }
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# ------------------------#
# CLOUDFRONT DISTRIBUTION #
# ------------------------#

resource "aws_cloudfront_distribution" "frontend_distribution" {
  origin {
    domain_name = aws_s3_bucket_website_configuration.frontend_website.website_endpoint
    origin_id   = "S3-${aws_s3_bucket.frontend_bucket.bucket}"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.frontend_bucket.bucket}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

}

# -----------------#
# DYNAMODB TABLES  #
# -----------------#

resource "aws_dynamodb_table" "car_park_users" {
  name         = var.users_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "UserID"
  
  attribute {
    name = "UserID"
    type = "S"
  }
  
  attribute {
    name = "CarRegistration"
    type = "S"
  }
  
  global_secondary_index {
    name               = "CarRegistrationIndex"
    hash_key           = "CarRegistration"
    projection_type    = "ALL"
  }

}

resource "aws_dynamodb_table" "parking_sessions" {
  name           = "ParkingSessions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "SessionID"
  
  attribute {
    name = "SessionID"
    type = "S"
  }
  
  attribute {
    name = "CarRegistration"
    type = "S"
  }
  
  attribute {
    name = "EntryTime"
    type = "N"
  }
  
  global_secondary_index {
    name               = "CarRegistrationIndex"
    hash_key           = "CarRegistration"
    projection_type    = "ALL"
  }
  
  global_secondary_index {
    name               = "EntryTimeIndex"
    hash_key           = "EntryTime"
    projection_type    = "ALL"
  }
  
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
}

# -----------------------#
# DYNAMODB STREAM EVENTS #
# -----------------------#

resource "aws_lambda_event_source_mapping" "dynamodb_stream_mapping" {
  event_source_arn  = aws_dynamodb_table.parking_sessions.stream_arn
  function_name     = aws_lambda_function.notifications.function_name
  starting_position = "LATEST"
  batch_size        = 1
  enabled           = true
}

resource "aws_lambda_permission" "allow_dynamodb" {
  statement_id  = "AllowExecutionFromDynamoDB"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifications.function_name
  principal     = "dynamodb.amazonaws.com"
  source_arn    = aws_dynamodb_table.parking_sessions.stream_arn
}

# -----------------#
# SNS TOPICS       #
# -----------------#

resource "aws_sns_topic" "payment_notifications" {
  name = "car-park-payment-notifications"
}

resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.payment_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
  
  count     = var.notification_email != "" ? 1 : 0
}

# -----------------#
# LAMBDA FUNCTIONS #
# -----------------#

resource "aws_lambda_function" "notifications" {
  function_name    = "car-park-notifications"
  filename         = data.archive_file.notifications_zip.output_path
  source_code_hash = data.archive_file.notifications_zip.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  handler          = "notifications.lambda_handler"
  runtime          = "python3.10"
  timeout          = 15
  memory_size      = 128

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.payment_notifications.arn
    }
  }
}

resource "aws_lambda_function" "s3getpassrek" {
  function_name    = "car-park-image-processing"
  filename         = data.archive_file.s3getpassrek_zip.output_path
  source_code_hash = data.archive_file.s3getpassrek_zip.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  handler          = "s3getpassrek.main"
  runtime          = "python3.10"
  timeout          = 15
  memory_size      = 128

  environment {
    variables = {
      IMAGES_BUCKET  = aws_s3_bucket.car_images_bucket.bucket
      USERS_TABLE    = aws_dynamodb_table.car_park_users.name
      SESSIONS_TABLE = aws_dynamodb_table.parking_sessions.name
    }
  }
}

resource "aws_lambda_function" "regplateapi" {
  function_name    = "car-park-reg-plate-api"
  filename         = data.archive_file.regplateapi_zip.output_path
  source_code_hash = data.archive_file.regplateapi_zip.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  handler          = "regplateapi.main"
  runtime          = "python3.10"
  timeout          = 15
  memory_size      = 128

  environment {
    variables = {
      USERS_TABLE    = aws_dynamodb_table.car_park_users.name
      SESSIONS_TABLE = aws_dynamodb_table.parking_sessions.name
    }
  }
}

resource "aws_lambda_function" "user_profile" {
  function_name    = "car-park-user-profile"
  filename         = data.archive_file.user_profile_zip.output_path
  source_code_hash = data.archive_file.user_profile_zip.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  handler          = "user_profile.main"
  runtime          = "python3.10"
  timeout          = 15
  memory_size      = 128

  environment {
    variables = {
      USERS_TABLE    = aws_dynamodb_table.car_park_users.name
      SNS_TOPIC_ARN  = aws_sns_topic.payment_notifications.arn
    }
  }
}

# ------------------#
# S3 EVENT TRIGGERS #
# ------------------#

resource "aws_s3_bucket_notification" "car_images_notification" {
  bucket = aws_s3_bucket.car_images_bucket.id
  
  lambda_function {
    lambda_function_arn = aws_lambda_function.s3getpassrek.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
  }
  
  depends_on = [
    aws_lambda_permission.allow_s3,
    aws_lambda_function.s3getpassrek,
    aws_s3_object.uploads_folder
  ]
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3getpassrek.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.car_images_bucket.arn
}

# -----------------#
# API GATEWAY      #
# -----------------#

resource "aws_apigatewayv2_api" "car_park_api" {
  name          = var.api_name
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_stage" "car_park_api_stage" {
  api_id      = aws_apigatewayv2_api.car_park_api.id
  name        = var.api_stage_name
  auto_deploy = true
}

# -------------------------#
# API GATEWAY INTEGRATIONS #
# ------------------------#

resource "aws_apigatewayv2_integration" "regplateapi_integration" {
  api_id             = aws_apigatewayv2_api.car_park_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.regplateapi.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "regplateapi_route" {
  api_id    = aws_apigatewayv2_api.car_park_api.id
  route_key = "POST /regplate"
  target    = "integrations/${aws_apigatewayv2_integration.regplateapi_integration.id}"
}

resource "aws_lambda_permission" "api_gateway_regplateapi" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.regplateapi.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.car_park_api.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "notifications_integration" {
  api_id             = aws_apigatewayv2_api.car_park_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.notifications.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "notifications_route" {
  api_id    = aws_apigatewayv2_api.car_park_api.id
  route_key = "POST /notify"
  target    = "integrations/${aws_apigatewayv2_integration.notifications_integration.id}"
}

resource "aws_lambda_permission" "api_gateway_notifications" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifications.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.car_park_api.execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "user_profile_integration" {
  api_id           = aws_apigatewayv2_api.car_park_api.id
  integration_type = "AWS_PROXY"
  
  integration_uri    = aws_lambda_function.user_profile.invoke_arn
  integration_method = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "profile_post_route" {
  api_id    = aws_apigatewayv2_api.car_park_api.id
  route_key = "POST /profile"
  
  target = "integrations/${aws_apigatewayv2_integration.user_profile_integration.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito_authorizer.id
}

resource "aws_apigatewayv2_route" "profile_get_route" {
  api_id    = aws_apigatewayv2_api.car_park_api.id
  route_key = "GET /profile"
  
  target = "integrations/${aws_apigatewayv2_integration.user_profile_integration.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito_authorizer.id
}

resource "aws_apigatewayv2_route" "profile_put_route" {
  api_id    = aws_apigatewayv2_api.car_park_api.id
  route_key = "PUT /profile"
  
  target = "integrations/${aws_apigatewayv2_integration.user_profile_integration.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.cognito_authorizer.id
}

resource "aws_apigatewayv2_authorizer" "cognito_authorizer" {
  api_id           = aws_apigatewayv2_api.car_park_api.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-authorizer"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.car_park_client.id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.car_park_users_pool.id}"
  }
}

resource "aws_lambda_permission" "api_gateway_user_profile" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.user_profile.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_apigatewayv2_api.car_park_api.execution_arn}/*/*"
}

# -------------------------#
# COGNITO USER POOLS       #
# -------------------------#

resource "aws_cognito_user_pool" "car_park_users_pool" {
  name = "car-park-users-pool"
  
  auto_verified_attributes = ["email"]
  
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }
  
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject = "Your verification code"
    email_message = "Your verification code is {####}"
  }
  
  password_policy {
    minimum_length = 8
    require_lowercase = true
    require_numbers = true
    require_uppercase = true
    require_symbols = false
  }
  
  schema {
    name = "email"
    attribute_data_type = "String"
    mutable = true
    required = true
  }

  lambda_config {
    post_confirmation = aws_lambda_function.user_profile.arn
  }
}

resource "aws_cognito_user_pool_client" "car_park_client" {
  name = "car-park-client"
  user_pool_id = aws_cognito_user_pool.car_park_users_pool.id
  
  generate_secret = false
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]
  
  callback_urls = ["https://${aws_cloudfront_distribution.frontend_distribution.domain_name}"]
  logout_urls = ["https://${aws_cloudfront_distribution.frontend_distribution.domain_name}"]
  
  allowed_oauth_flows = ["implicit"]
  allowed_oauth_scopes = ["email", "openid", "profile"]
  supported_identity_providers = ["COGNITO"]
}

resource "aws_lambda_permission" "allow_cognito_user_profile" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.user_profile.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.car_park_users_pool.arn
}