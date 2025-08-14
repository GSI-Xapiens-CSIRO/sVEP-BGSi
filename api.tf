#
# API Gateway
#
resource "aws_api_gateway_rest_api" "VPApi" {
  name        = "svep-backend-api"
  description = "API That implements the Variant Prioritization specification"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# 
# /submit
# 
resource "aws_api_gateway_resource" "submit" {
  rest_api_id = aws_api_gateway_rest_api.VPApi.id
  parent_id   = aws_api_gateway_rest_api.VPApi.root_resource_id
  path_part   = "submit"
}

resource "aws_api_gateway_method" "submit-options" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "submit-options" {
  rest_api_id = aws_api_gateway_method.submit-options.rest_api_id
  resource_id = aws_api_gateway_method.submit-options.resource_id
  http_method = aws_api_gateway_method.submit-options.http_method
  status_code = aws_api_gateway_method_response.submit-options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,PATCH,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-options]
}

resource "aws_api_gateway_method" "submit-patch" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "PATCH"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.svep_user_pool_authorizer.id
}

resource "aws_api_gateway_method_response" "submit-patch" {
  rest_api_id = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id = aws_api_gateway_method.submit-patch.resource_id
  http_method = aws_api_gateway_method.submit-patch.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-patch" {
  rest_api_id             = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id             = aws_api_gateway_method.submit-patch.resource_id
  http_method             = aws_api_gateway_method.submit-patch.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-initQuery.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "submit-patch" {
  rest_api_id = aws_api_gateway_method.submit-patch.rest_api_id
  resource_id = aws_api_gateway_method.submit-patch.resource_id
  http_method = aws_api_gateway_method.submit-patch.http_method
  status_code = aws_api_gateway_method_response.submit-patch.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-patch]
}

resource "aws_api_gateway_method" "submit-post" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.submit.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.svep_user_pool_authorizer.id
}

resource "aws_api_gateway_method_response" "submit-post" {
  rest_api_id = aws_api_gateway_method.submit-post.rest_api_id
  resource_id = aws_api_gateway_method.submit-post.resource_id
  http_method = aws_api_gateway_method.submit-post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "submit-post" {
  rest_api_id             = aws_api_gateway_method.submit-post.rest_api_id
  resource_id             = aws_api_gateway_method.submit-post.resource_id
  http_method             = aws_api_gateway_method.submit-post.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-initQuery.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "submit-post" {
  rest_api_id = aws_api_gateway_method.submit-post.rest_api_id
  resource_id = aws_api_gateway_method.submit-post.resource_id
  http_method = aws_api_gateway_method.submit-post.http_method
  status_code = aws_api_gateway_method_response.submit-post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.submit-post]
}

# 
# /results
# 
resource "aws_api_gateway_resource" "results" {
  rest_api_id = aws_api_gateway_rest_api.VPApi.id
  parent_id   = aws_api_gateway_rest_api.VPApi.root_resource_id
  path_part   = "results"
}

resource "aws_api_gateway_method" "results-options" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.results.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "results-options" {
  rest_api_id = aws_api_gateway_method.results-options.rest_api_id
  resource_id = aws_api_gateway_method.results-options.resource_id
  http_method = aws_api_gateway_method.results-options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "results-options" {
  rest_api_id = aws_api_gateway_method.results-options.rest_api_id
  resource_id = aws_api_gateway_method.results-options.resource_id
  http_method = aws_api_gateway_method.results-options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "results-options" {
  rest_api_id = aws_api_gateway_method.results-options.rest_api_id
  resource_id = aws_api_gateway_method.results-options.resource_id
  http_method = aws_api_gateway_method.results-options.http_method
  status_code = aws_api_gateway_method_response.results-options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.results-options]
}

resource "aws_api_gateway_method" "results-get" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.results.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.svep_user_pool_authorizer.id
}

resource "aws_api_gateway_method_response" "results-get" {
  rest_api_id = aws_api_gateway_method.results-get.rest_api_id
  resource_id = aws_api_gateway_method.results-get.resource_id
  http_method = aws_api_gateway_method.results-get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "results-get" {
  rest_api_id             = aws_api_gateway_method.results-get.rest_api_id
  resource_id             = aws_api_gateway_method.results-get.resource_id
  http_method             = aws_api_gateway_method.results-get.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getResultsURL.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "results-get" {
  rest_api_id = aws_api_gateway_method.results-get.rest_api_id
  resource_id = aws_api_gateway_method.results-get.resource_id
  http_method = aws_api_gateway_method.results-get.http_method
  status_code = aws_api_gateway_method_response.results-get.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.results-get]
}

#
# /batch-submit
#
resource "aws_api_gateway_resource" "batch-submit" {
  rest_api_id = aws_api_gateway_rest_api.VPApi.id
  parent_id   = aws_api_gateway_rest_api.VPApi.root_resource_id
  path_part   = "batch-submit"
}

resource "aws_api_gateway_method" "batch-submit-post" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.batch-submit.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.svep_user_pool_authorizer.id
}

resource "aws_api_gateway_method_response" "batch-submit-post" {
  rest_api_id = aws_api_gateway_method.batch-submit-post.rest_api_id
  resource_id = aws_api_gateway_method.batch-submit-post.resource_id
  http_method = aws_api_gateway_method.batch-submit-post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "batch-submit-post" {
  rest_api_id             = aws_api_gateway_method.batch-submit-post.rest_api_id
  resource_id             = aws_api_gateway_method.batch-submit-post.resource_id
  http_method             = aws_api_gateway_method.batch-submit-post.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-batchSubmit.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "batch-submit-post" {
  rest_api_id = aws_api_gateway_method.batch-submit-post.rest_api_id
  resource_id = aws_api_gateway_method.batch-submit-post.resource_id
  http_method = aws_api_gateway_method.batch-submit-post.http_method
  status_code = aws_api_gateway_method_response.batch-submit-post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.batch-submit-post]
}

resource "aws_api_gateway_method" "batch-submit-options" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.batch-submit.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "batch-submit-options" {
  rest_api_id = aws_api_gateway_method.batch-submit-options.rest_api_id
  resource_id = aws_api_gateway_method.batch-submit-options.resource_id
  http_method = aws_api_gateway_method.batch-submit-options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "batch-submit-options" {
  rest_api_id = aws_api_gateway_method.batch-submit-options.rest_api_id
  resource_id = aws_api_gateway_method.batch-submit-options.resource_id
  http_method = aws_api_gateway_method.batch-submit-options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "batch-submit-options" {
  rest_api_id = aws_api_gateway_method.batch-submit-options.rest_api_id
  resource_id = aws_api_gateway_method.batch-submit-options.resource_id
  http_method = aws_api_gateway_method.batch-submit-options.http_method
  status_code = aws_api_gateway_method_response.batch-submit-options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,PATCH,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.batch-submit-options]
}


#
# Vcfstats
#
resource "aws_api_gateway_resource" "vcfstats" {
  rest_api_id = aws_api_gateway_rest_api.VPApi.id
  parent_id   = aws_api_gateway_rest_api.VPApi.root_resource_id
  path_part   = "vcfstats"
}

resource "aws_api_gateway_method" "vcfstats-post" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.vcfstats.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.svep_user_pool_authorizer.id
}
resource "aws_api_gateway_method_response" "vcfstats-post" {
  rest_api_id = aws_api_gateway_method.vcfstats-post.rest_api_id
  resource_id = aws_api_gateway_method.vcfstats-post.resource_id
  http_method = aws_api_gateway_method.vcfstats-post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "vcfstats-post" {
  rest_api_id             = aws_api_gateway_method.vcfstats-post.rest_api_id
  resource_id             = aws_api_gateway_method.vcfstats-post.resource_id
  http_method             = aws_api_gateway_method.vcfstats-post.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-qcFigures.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "vcfstats-post" {
  rest_api_id = aws_api_gateway_method.vcfstats-post.rest_api_id
  resource_id = aws_api_gateway_method.vcfstats-post.resource_id
  http_method = aws_api_gateway_method.vcfstats-post.http_method
  status_code = aws_api_gateway_method_response.vcfstats-post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.vcfstats-post]
}

resource "aws_api_gateway_method" "vcfstats-options" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.vcfstats.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "vcfstats-options" {
  rest_api_id = aws_api_gateway_method.vcfstats-options.rest_api_id
  resource_id = aws_api_gateway_method.vcfstats-options.resource_id
  http_method = aws_api_gateway_method.vcfstats-options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "vcfstats-options" {
  rest_api_id = aws_api_gateway_method.vcfstats-options.rest_api_id
  resource_id = aws_api_gateway_method.vcfstats-options.resource_id
  http_method = aws_api_gateway_method.vcfstats-options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "vcfstats-options" {
  rest_api_id = aws_api_gateway_method.vcfstats-options.rest_api_id
  resource_id = aws_api_gateway_method.vcfstats-options.resource_id
  http_method = aws_api_gateway_method.vcfstats-options.http_method
  status_code = aws_api_gateway_method_response.vcfstats-options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,PATCH,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.vcfstats-options]
}

resource "aws_api_gateway_method" "vcfstats-patch" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.vcfstats.id
  http_method   = "PATCH"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.svep_user_pool_authorizer.id
}

resource "aws_api_gateway_method_response" "vcfstats-patch" {
  rest_api_id = aws_api_gateway_method.vcfstats-patch.rest_api_id
  resource_id = aws_api_gateway_method.vcfstats-patch.resource_id
  http_method = aws_api_gateway_method.vcfstats-patch.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "vcfstats-patch" {
  rest_api_id             = aws_api_gateway_method.vcfstats-patch.rest_api_id
  resource_id             = aws_api_gateway_method.vcfstats-patch.resource_id
  http_method             = aws_api_gateway_method.vcfstats-patch.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-qcFigures.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "vcfstats-patch" {
  rest_api_id = aws_api_gateway_method.vcfstats-patch.rest_api_id
  resource_id = aws_api_gateway_method.vcfstats-patch.resource_id
  http_method = aws_api_gateway_method.vcfstats-patch.http_method
  status_code = aws_api_gateway_method_response.vcfstats-patch.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.vcfstats-patch]
}

#
# Deployment
#
resource "aws_api_gateway_deployment" "VPApi" {
  rest_api_id = aws_api_gateway_rest_api.VPApi.id
  # Without enabling create_before_destroy, 
  # API Gateway can return errors such as BadRequestException: 
  # Active stages pointing to this deployment must be moved or deleted on recreation.
  lifecycle {
    create_before_destroy = true
  }
  # taint deployment if any api resources change
  triggers = {
    redeployment = sha1(jsonencode([
      # /submit
      aws_api_gateway_method.submit-options,
      aws_api_gateway_integration.submit-options,
      aws_api_gateway_integration_response.submit-options,
      aws_api_gateway_method_response.submit-options,
      aws_api_gateway_method.submit-patch,
      aws_api_gateway_integration.submit-patch,
      aws_api_gateway_integration_response.submit-patch,
      aws_api_gateway_method_response.submit-patch,
      aws_api_gateway_method.submit-post,
      aws_api_gateway_integration.submit-post,
      aws_api_gateway_integration_response.submit-post,
      aws_api_gateway_method_response.submit-post,
      # /results
      aws_api_gateway_method.results-options,
      aws_api_gateway_integration.results-options,
      aws_api_gateway_integration_response.results-options,
      aws_api_gateway_method_response.results-options,
      aws_api_gateway_method.results-get,
      aws_api_gateway_integration.results-get,
      aws_api_gateway_integration_response.results-get,
      aws_api_gateway_method_response.results-get,
      # /batch-submit
      aws_api_gateway_method.batch-submit-options,
      aws_api_gateway_integration.batch-submit-options,
      aws_api_gateway_integration_response.batch-submit-options,
      aws_api_gateway_method_response.batch-submit-options,
      aws_api_gateway_method.batch-submit-post,
      aws_api_gateway_integration.batch-submit-post,
      aws_api_gateway_integration_response.batch-submit-post,
      aws_api_gateway_method_response.batch-submit-post,
      # /vcfstats
      aws_api_gateway_method.vcfstats-options,
      aws_api_gateway_integration.vcfstats-options,
      aws_api_gateway_integration_response.vcfstats-options,
      aws_api_gateway_method_response.vcfstats-options,
      aws_api_gateway_method.vcfstats-patch,
      aws_api_gateway_integration.vcfstats-patch,
      aws_api_gateway_integration_response.vcfstats-patch,
      aws_api_gateway_method_response.vcfstats-patch,
      aws_api_gateway_method.vcfstats-post,
      aws_api_gateway_method_response.vcfstats-post,
      aws_api_gateway_integration.vcfstats-post,
      aws_api_gateway_integration_response.vcfstats-post,
      # /qcnotes
      aws_api_gateway_method.qcnotes-options,
      aws_api_gateway_integration.qcnotes-options,
      aws_api_gateway_integration_response.qcnotes-options,
      aws_api_gateway_method_response.qcnotes-options,
      aws_api_gateway_method.qcnotes-post,
      aws_api_gateway_integration.qcnotes-post,
      aws_api_gateway_integration_response.qcnotes-post,
      aws_api_gateway_method_response.qcnotes-post,
      aws_api_gateway_method.qcnotes-get,
      aws_api_gateway_integration.qcnotes-get,
      aws_api_gateway_integration_response.qcnotes-get,
      aws_api_gateway_method_response.qcnotes-get,
    ]))
  }
}

resource "aws_api_gateway_stage" "VPApi" {
  deployment_id = aws_api_gateway_deployment.VPApi.id
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  stage_name    = "prod"
}

resource "aws_api_gateway_method_settings" "VPApi" {
  rest_api_id = aws_api_gateway_rest_api.VPApi.id
  stage_name  = aws_api_gateway_stage.VPApi.stage_name
  method_path = "*/*"

  settings {
    throttling_burst_limit = var.method-queue-size
    throttling_rate_limit  = var.method-max-request-rate
  }
}
