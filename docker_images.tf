#
# pluginConsequence docker image
#
data "external" "pluginConsequence_lambda_source_hash" {
  program     = ["python", "lambda/pluginConsequence/docker_prep.py"]
  working_dir = path.module
}

module "docker_image_pluginConsequence_lambda" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = true
  ecr_repo        = "svep-pluginconsequence-lambda-containers"
  ecr_repo_lifecycle_policy = jsonencode({
    "rules" : [
      {
        "rulePriority" : 1,
        "description" : "Keep only the last 1 images",
        "selection" : {
          "tagStatus" : "any",
          "countType" : "imageCountMoreThan",
          "countNumber" : 1
        },
        "action" : {
          "type" : "expire"
        }
      }
    ]
  })
  use_image_tag = false
  source_path   = "${path.module}/lambda/pluginConsequence"

  triggers = {
    dir_sha = data.external.pluginConsequence_lambda_source_hash.result.hash
  }

  platform = "linux/amd64"
}

#
# qcFigures docker image
#
data "external" "qcFigures_lambda_source_hash" {
  program     = ["python", "lambda/qcFigures/docker_prep.py"]
  working_dir = path.module
}

module "docker_image_qcFigures_lambda" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = true
  ecr_repo        = "svep-qcfigures-lambda-containers"
  ecr_repo_lifecycle_policy = jsonencode({
    "rules" : [
      {
        "rulePriority" : 1,
        "description" : "Keep only the last 1 images",
        "selection" : {
          "tagStatus" : "any",
          "countType" : "imageCountMoreThan",
          "countNumber" : 1
        },
        "action" : {
          "type" : "expire"
        }
      }
    ]
  })
  use_image_tag = false
  build_args = {
    SHARED_LAYER_PATH = "${path.module}/shared_resources/python-modules/python/shared"
  }
  source_path = "${path.module}/lambda/qcFigures"

  triggers = {
    dir_sha = data.external.qcFigures_lambda_source_hash.result.hash
  }

  platform = "linux/amd64"
}
