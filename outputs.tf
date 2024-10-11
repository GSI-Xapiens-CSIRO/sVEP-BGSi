output "backend_api_url" {
  value = module.svep-backend.api_url
  description = "URL used to invoke the backend API."
}

output "frontend_api_url" {
  value = module.svep-frontend.api_url
  description = "URL used to invoke the frontend API."
}

output "cloudfront_url" {
  value = module.svep-frontend.cloudfront_url
  description = "Cloudfront url."
}