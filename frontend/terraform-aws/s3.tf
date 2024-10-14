# bucket definition
resource "aws_s3_bucket" "svep_hosted_bucket" {
  bucket_prefix = "svep-frontend-bucket-"

  tags = var.common-tags
}

resource "aws_s3_bucket_lifecycle_configuration" "svep_hosted_bucket_cycle" {
  bucket = aws_s3_bucket.svep_hosted_bucket.id

  rule {
    id     = "svep-frontend-data-bucket-delete-old"
    status = "Enabled"

    filter {
      prefix = "uploads/"
    }

    expiration {
      days = 3
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "svep_hosted_bucket_cycle_config" {
  bucket = aws_s3_bucket.svep_hosted_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST"]
    allowed_origins = ["*"]
    expose_headers  = []
    max_age_seconds = 3000
  }
}

# allow cloudfront to access s3
resource "aws_s3_bucket_policy" "s3_access_from_cloudfront" {
  bucket = aws_s3_bucket.svep_hosted_bucket.id
  policy = data.aws_iam_policy_document.s3_access_from_cloudfront.json
}

# iam policy
data "aws_iam_policy_document" "s3_access_from_cloudfront" {
  statement {
    principals {
      type = "Service"
      identifiers = [
        "cloudfront.amazonaws.com"
      ]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.svep_hosted_bucket.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values = [
        aws_cloudfront_distribution.svep_s3_distribution.arn
      ]
    }
  }
}
