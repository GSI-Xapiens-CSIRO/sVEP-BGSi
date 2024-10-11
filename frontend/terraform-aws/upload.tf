data "external" "build" {
  program     = ["python", "build_and_hash.py"]
  query = {
    install_command = var.install-command
    build_command = var.build-command
    webapp_dir = var.webapp-dir
    build_destiation = var.build-destination
    backend_api_url = var.backend_api_url
    frontend_api_url = aws_api_gateway_deployment.svep_ui.invoke_url
    cloudfront_url = aws_cloudfront_distribution.svep_s3_distribution.domain_name
  }
  working_dir = path.module
}

resource "null_resource" "s3_upload" {
  triggers = {
    compiled_code_hash = data.external.build.result.hash
    build_file_hash = filesha1("${path.module}/build_and_hash.py")
  }

  provisioner "local-exec" {
    command = "/bin/bash ${path.module}/upload.sh ${path.module}/${var.build-destination} ${aws_s3_bucket.svep_hosted_bucket.id}"
  }

  depends_on = [
    aws_s3_bucket.svep_hosted_bucket
  ]
}

resource "null_resource" "cloudfront_invalidate" {
  triggers = {
    compiled_code_hash = data.external.build.result.hash
  }

  provisioner "local-exec" {
    command = "aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.svep_s3_distribution.id} --paths '/*'"
  }

  depends_on = [
    null_resource.s3_upload,
  ]
}
