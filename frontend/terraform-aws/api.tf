#
# API Gateway
#
resource "aws_api_gateway_rest_api" "svep_ui" {
  name        = "svep-frontend-api"
  description = "sVEP UI API"
}

#
# Deployment
#
resource "aws_api_gateway_deployment" "svep_ui" {
  rest_api_id = aws_api_gateway_rest_api.svep_ui.id
  stage_name    = "prod"

  lifecycle {
    create_before_destroy = true
  }

  stage_description = "Deployment for sVEP UI API"

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.svep_ui_proxy,
      aws_api_gateway_method.any_svep_ui_proxy,
      aws_api_gateway_method_response.any_svep_ui_proxy,
      aws_api_gateway_integration.any_svep_ui_proxy,
    ]))
  }

  depends_on = [
    aws_api_gateway_integration.any_svep_ui_proxy
  ]
}

#
# API Function {proxy+}
#
resource "aws_api_gateway_resource" "svep_ui_proxy" {
  path_part   = "{proxy+}"
  parent_id   = aws_api_gateway_rest_api.svep_ui.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.svep_ui.id
}

# ANY
resource "aws_api_gateway_method" "any_svep_ui_proxy" {
  rest_api_id   = aws_api_gateway_resource.svep_ui_proxy.rest_api_id
  resource_id   = aws_api_gateway_resource.svep_ui_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "any_svep_ui_proxy" {
  rest_api_id = aws_api_gateway_method.any_svep_ui_proxy.rest_api_id
  resource_id = aws_api_gateway_method.any_svep_ui_proxy.resource_id
  http_method = aws_api_gateway_method.any_svep_ui_proxy.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# 
# CORS
# 
module "cors-svep_ui_proxy" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.svep_ui.id
  api_resource_id = aws_api_gateway_resource.svep_ui_proxy.id
}

# 
# Integrations
# 
resource "aws_api_gateway_integration" "any_svep_ui_proxy" {
  rest_api_id             = aws_api_gateway_rest_api.svep_ui.id
  resource_id             = aws_api_gateway_resource.svep_ui_proxy.id
  http_method             = aws_api_gateway_method.any_svep_ui_proxy.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda_function.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "any_svep_ui_proxy" {
  rest_api_id = aws_api_gateway_integration.any_svep_ui_proxy.rest_api_id
  resource_id = aws_api_gateway_integration.any_svep_ui_proxy.resource_id
  http_method = aws_api_gateway_integration.any_svep_ui_proxy.http_method
  status_code = aws_api_gateway_method_response.any_svep_ui_proxy.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.any_svep_ui_proxy]
}

# 
# Permissions
# 
resource "aws_lambda_permission" "any-admin" {
  statement_id  = "api-allow-admin"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_function.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.svep_ui.execution_arn}/*"
}
