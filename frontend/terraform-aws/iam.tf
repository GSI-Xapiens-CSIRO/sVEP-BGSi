# lambda_s3_full_access
data "aws_iam_policy_document" "lambda_s3_full_access" {
  statement {
    actions = [
      "s3:*",
    ]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.svep_hosted_bucket.id}",
      "arn:aws:s3:::${aws_s3_bucket.svep_hosted_bucket.id}/*"
    ]
  }
}