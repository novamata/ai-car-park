output "frontend_bucket_website_endpoint" {
  value = aws_s3_bucket_website_configuration.frontend_website.website_endpoint
}

output "cloudfront_distribution_domain" {
  value = aws_cloudfront_distribution.frontend_distribution.domain_name
}

output "api_gateway_url" {
  value = "${aws_apigatewayv2_stage.car_park_api_stage.invoke_url}"
}

