### binaries layer
# data for the binaries_layer layer
data "archive_file" "binaries_layer" {
  type        = "zip"
  source_dir  = "${path.module}/layers/binaries/"
  output_path = "${path.module}/binaries.zip"

  depends_on = [null_resource.init_script]
}

# binaries layer definition
resource "aws_lambda_layer_version" "binaries_layer" {
  filename         = data.archive_file.binaries_layer.output_path
  layer_name       = "svep_backend_binaries_layer"
  source_code_hash = data.archive_file.binaries_layer.output_base64sha512

  compatible_runtimes = ["python3.12"]
}

### python thirdparty libraries layer 
# contains pynamodb, jsons, jsonschema, smart_open
/*module "python_libraries_layer" {
  source = "terraform-aws-modules/lambda/aws"

  create_layer = true

  layer_name          = "svep_backend_python_libraries_layer"
  description         = "python libraries"
  compatible_runtimes = ["python3.12"]

  source_path = "${path.module}/layers/python_libraries/"

  store_on_s3 = true
  s3_bucket   = aws_s3_bucket.lambda-layers-bucket.bucket
}*/

### python first party modules layer 
module "python_modules_layer" {
  source = "terraform-aws-modules/lambda/aws"

  create_layer = true

  layer_name          = "svep_backend_python_modules_layer"
  description         = "python libraries"
  compatible_runtimes = ["python3.12"]

  source_path = "${path.module}/shared_resources/python-modules/"

  store_on_s3 = true
  s3_bucket   = aws_s3_bucket.lambda-layers-bucket.bucket
}

# Archive Hail Layer
# data "archive_file" "hail_layer" {
#   type        = "zip"
#   source_dir  = "${path.module}/layers/hail/"
#   output_path = "${path.module}/hail.zip"

#   depends_on = [null_resource.init_gnomad_script]
# }

# # Create Hail Lambda Layer
# resource "aws_lambda_layer_version" "hail_layer" {
#   filename         = data.archive_file.hail_layer.output_path
#   layer_name       = "hail-layer"
#   description      = "Hail library for genomics"
#   source_code_hash = filebase64sha256(data.archive_file.hail_layer.output_path)

#   compatible_runtimes = ["python3.12"]

#   depends_on = [data.archive_file.hail_layer]
# }