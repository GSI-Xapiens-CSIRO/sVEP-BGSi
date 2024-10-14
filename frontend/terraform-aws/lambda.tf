module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "svep-frontend-url-generator"
  description         = "Functions to generate signed URLs for uploads"
  handler             = "handler.lambda_handler"
  runtime             = "nodejs18.x"
  memory_size         = 256
  timeout             = 6
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda_s3_full_access.json,
  ]
  number_of_policy_jsons = 1
  environment_variables = {
    BUCKET_NAME  = aws_s3_bucket.svep_hosted_bucket.id
    NODE_OPTIONS = "--enable-source-maps"
  }
  source_path = [
    {
      path = "${path.module}/../ui-backend/lambda",
      commands = [
        "pnpm install",
        "./node_modules/.bin/esbuild --sourcemap --bundle handler.js --outdir=dist --platform=node --target=node18 --preserve-symlinks --external:@aws-sdk/client-s3 --external:@aws-sdk/s3-presigned-post",
        "cd dist",
        ":zip"
      ]
    }
  ]

  tags = var.common-tags
}
