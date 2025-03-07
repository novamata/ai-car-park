variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "frontend_bucket_prefix" {
  description = "Prefix for the S3 bucket that hosts the frontend"
  type        = string
}

variable "car_images_bucket_prefix" {
  description = "Prefix for the S3 bucket that stores car images"
  type        = string
}

variable "users_table_name" {
  description = "Name of the DynamoDB table for car park users"
  type        = string
}

variable "sessions_table_name" {
  description = "Name of the DynamoDB table for parking sessions"
  type        = string
}

variable "api_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "api_stage_name" {
  description = "Name of the API Gateway stage"
  type        = string
}

variable "notification_email" {
  description = "Email address to receive parking payment notifications"
  type        = string
}
