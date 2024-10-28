resource "aws_s3_bucket" "svep-inputs" {
  bucket_prefix = "svep-backend-inputs-"
  force_destroy = false
  tags = var.common-tags
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
