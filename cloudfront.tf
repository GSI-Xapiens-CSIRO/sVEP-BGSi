locals {
    api_gateway_origin_id = "svep-backend-api"
}

resource "aws_cloudfront_cache_policy" "api" {
  name        = "svep-backend-api"
  min_ttl     = 0
  default_ttl = 0
  max_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
  }
}

resource "aws_cloudfront_origin_request_policy" "api" {
  name = "svep-backend-api"

    cookies_config {
    cookie_behavior = "none"
  }

  headers_config {
    header_behavior = "allExcept"
    headers {
      items = ["Host"]
    }
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

resource "aws_cloudfront_distribution" "api_distribution" {
  origin {
    domain_name = split("/", aws_api_gateway_deployment.VPApi.invoke_url)[2]
    origin_id   = local.api_gateway_origin_id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  comment    = "svep-backend-api"
  enabled    = true
  web_acl_id = var.web_acl_arn

  default_cache_behavior {
    allowed_methods          = ["HEAD", "DELETE", "POST", "GET", "OPTIONS", "PUT", "PATCH"]
    cached_methods           = ["HEAD", "GET"]  # Just so terraform actually sets the CachedMethods parameter
    target_origin_id         = local.api_gateway_origin_id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api.id
    cache_policy_id          = aws_cloudfront_cache_policy.api.id
    viewer_protocol_policy   = "https-only"
    min_ttl                  = 0
    default_ttl              = 0
    max_ttl                  = 0
  }

  restrictions {
    geo_restriction {
      locations        = []
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
