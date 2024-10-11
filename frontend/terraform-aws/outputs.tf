output "api_url" {
  value = aws_api_gateway_deployment.svep_ui.invoke_url
  description = "API endpoint"
}

output "cloudfront_url" {
  value = "https://${aws_cloudfront_distribution.svep_s3_distribution.domain_name}"
  description = "Cloudfront url"
}