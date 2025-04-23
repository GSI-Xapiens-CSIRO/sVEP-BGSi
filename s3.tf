resource "aws_s3_bucket" "svep-inputs" {
  bucket_prefix = "svep-backend-inputs-"
  force_destroy = false
  tags          = var.common-tags
}

resource "aws_s3_bucket" "svep-regions" {
  bucket_prefix = "svep-backend-regions-"
  force_destroy = true
  tags          = var.common-tags
}
resource "aws_s3_bucket" "svep-temp" {
  bucket_prefix = "svep-backend-temp-"
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket_lifecycle_configuration" "svep-temp-lifecycle" {
  bucket = aws_s3_bucket.svep-temp.id

  rule {
    id     = "remove-old-payloads"
    status = "Enabled"

    filter {
      prefix = "payloads/"
    }

    expiration {
      days = 1
    }
  }
}

resource "aws_s3_bucket" "svep-results" {
  bucket_prefix = "svep-backend-results-"
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket" "svep-references" {
  bucket_prefix = "svep-backend-references-"
  force_destroy = false
  tags          = var.common-tags
}

resource "aws_s3_bucket_cors_configuration" "svep-results-cors" {
  bucket = aws_s3_bucket.svep-results.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
    expose_headers  = []
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket" "lambda-layers-bucket" {
  bucket_prefix = "svep-backend-layers-"
  force_destroy = true
  tags          = var.common-tags
}
