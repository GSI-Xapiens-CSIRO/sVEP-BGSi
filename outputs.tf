output "api_url" {
  value       = "https://${aws_cloudfront_distribution.api_distribution.domain_name}/${aws_api_gateway_stage.VPApi.stage_name}/"
  description = "URL used to invoke the backend API."
}

output "send_job_email_lambda_function_arn" {
  value       = module.lambda-sendJobEmail.function_arn
  description = "Lambda function ARN for sending Jobs email"
}