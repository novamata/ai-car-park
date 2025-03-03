data "archive_file" "notifications_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/notifications.py"
  output_path = "${path.module}/notifications.zip"
}

data "archive_file" "s3getpassrek_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/s3getpassrek.py"
  output_path = "${path.module}/s3getpassrek.zip"
}

data "archive_file" "regplateapi_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/regplateapi.py"
  output_path = "${path.module}/regplateapi.zip"
}