resource "aws_cloudfront_origin_access_control" "svep_s3_distribution" {
  name                              = "svep-s3-access-control"
  description                       = "Policy for BeaconUI"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_cloudfront_cache_policy" "svep-s3-distribution-cache-policy" {
  name = "Managed-CachingOptimized"
}

resource "aws_cloudfront_cache_policy" "svep_cache_policy" {
  name = "svep-cache-policy"
  comment = "Policy for SVEP with presigned URLs"
  default_ttl = 50
  max_ttl = 100
  min_ttl = 1
  parameters_in_cache_key_and_forwarded_to_origin {
    query_strings_config {
      query_string_behavior = "all"
    }
    headers_config {
      header_behavior = "none"
    }
    cookies_config {
      cookie_behavior = "none"
    }
  }
}

resource "aws_cloudfront_distribution" "svep_s3_distribution" {
  origin {
    domain_name              = aws_s3_bucket.svep_hosted_bucket.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.svep_s3_distribution.id
    origin_id                = "svep-s3-origin-id"
    origin_path              = "/ui"
  }

  comment             = "Distribution for sVEP UI"
  enabled             = true
  is_ipv6_enabled     = true
  http_version        = "http2and3"
  default_root_object = "index.html"

  custom_error_response {
    response_code      = 200
    error_code         = 404
    response_page_path = "/index.html"
  }

  custom_error_response {
    response_code      = 200
    error_code         = 400
    response_page_path = "/index.html"
  }

  custom_error_response {
    response_code      = 200
    error_code         = 403
    response_page_path = "/index.html"
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "svep-s3-origin-id"
    cache_policy_id        = data.aws_cloudfront_cache_policy.svep-s3-distribution-cache-policy.id
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }

  price_class = "PriceClass_200"

  restrictions {
    geo_restriction {
      restriction_type = "none"
      locations        = []
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = var.common-tags
}
