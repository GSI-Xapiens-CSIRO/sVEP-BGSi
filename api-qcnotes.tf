#
# qcnotes
#
resource "aws_api_gateway_resource" "qcnotes" {
  rest_api_id = aws_api_gateway_rest_api.VPApi.id
  parent_id   = aws_api_gateway_rest_api.VPApi.root_resource_id
  path_part   = "qcnotes"
}

resource "aws_api_gateway_method" "qcnotes-post" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.qcnotes.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.svep_user_pool_authorizer.id
}

resource "aws_api_gateway_method_response" "qcnotes-post" {
  rest_api_id = aws_api_gateway_method.qcnotes-post.rest_api_id
  resource_id = aws_api_gateway_method.qcnotes-post.resource_id
  http_method = aws_api_gateway_method.qcnotes-post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "qcnotes-post" {
  rest_api_id             = aws_api_gateway_method.qcnotes-post.rest_api_id
  resource_id             = aws_api_gateway_method.qcnotes-post.resource_id
  http_method             = aws_api_gateway_method.qcnotes-post.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-qcNotes.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "qcnotes-post" {
  rest_api_id = aws_api_gateway_method.qcnotes-post.rest_api_id
  resource_id = aws_api_gateway_method.qcnotes-post.resource_id
  http_method = aws_api_gateway_method.qcnotes-post.http_method
  status_code = aws_api_gateway_method_response.qcnotes-post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.qcnotes-post]
}

resource "aws_api_gateway_method" "qcnotes-options" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.qcnotes.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "qcnotes-options" {
  rest_api_id = aws_api_gateway_method.qcnotes-options.rest_api_id
  resource_id = aws_api_gateway_method.qcnotes-options.resource_id
  http_method = aws_api_gateway_method.qcnotes-options.http_method
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

resource "aws_api_gateway_integration" "qcnotes-options" {
  rest_api_id = aws_api_gateway_method.qcnotes-options.rest_api_id
  resource_id = aws_api_gateway_method.qcnotes-options.resource_id
  http_method = aws_api_gateway_method.qcnotes-options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<TEMPLATE
      {
        "statusCode": 200
      }
    TEMPLATE
  }
}

resource "aws_api_gateway_integration_response" "qcnotes-options" {
  rest_api_id = aws_api_gateway_method.qcnotes-options.rest_api_id
  resource_id = aws_api_gateway_method.qcnotes-options.resource_id
  http_method = aws_api_gateway_method.qcnotes-options.http_method
  status_code = aws_api_gateway_method_response.qcnotes-options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.qcnotes-options]
}

resource "aws_api_gateway_method" "qcnotes-get" {
  rest_api_id   = aws_api_gateway_rest_api.VPApi.id
  resource_id   = aws_api_gateway_resource.qcnotes.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.svep_user_pool_authorizer.id
}

resource "aws_api_gateway_method_response" "qcnotes-get" {
  rest_api_id = aws_api_gateway_method.qcnotes-get.rest_api_id
  resource_id = aws_api_gateway_method.qcnotes-get.resource_id
  http_method = aws_api_gateway_method.qcnotes-get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "qcnotes-get" {
  rest_api_id             = aws_api_gateway_method.qcnotes-get.rest_api_id
  resource_id             = aws_api_gateway_method.qcnotes-get.resource_id
  http_method             = aws_api_gateway_method.qcnotes-get.http_method
  type                    = "AWS_PROXY"
  uri                     = module.lambda-qcNotes.lambda_function_invoke_arn
  integration_http_method = "POST"
}

resource "aws_api_gateway_integration_response" "qcnotes-get" {
  rest_api_id = aws_api_gateway_method.qcnotes-get.rest_api_id
  resource_id = aws_api_gateway_method.qcnotes-get.resource_id
  http_method = aws_api_gateway_method.qcnotes-get.http_method
  status_code = aws_api_gateway_method_response.qcnotes-get.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.qcnotes-get]
}
