output "api_url" {
  value       = "https://${aws_cloudfront_distribution.api_distribution.domain_name}/${aws_api_gateway_stage.VPApi.stage_name}/"
  description = "URL used to invoke the backend API."
}
