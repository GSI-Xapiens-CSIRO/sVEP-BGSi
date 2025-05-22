data "aws_caller_identity" "this" {}

locals {
  api_version     = "v1.0.0"
  slice_size_mbp  = 5
  result_suffix   = "_results.tsv"
  result_duration = 86400
  # layers
  binaries_layer = "${aws_lambda_layer_version.binaries_layer.layer_arn}:${aws_lambda_layer_version.binaries_layer.version}"
  // python_libraries_layer = module.python_libraries_layer.lambda_layer_arn
  python_modules_layer = module.python_modules_layer.lambda_layer_arn
  output_columns = join(",", [
    "rank",
    "region",
    "alt",
    "consequence",
    "varName",
    "geneName",
    "geneId",
    "feature",
    "transcriptId",
    "transcriptBiotype",
    "exonNumber",
    "aminoAcids",
    "codons",
    "strand",
    "transcriptSupportLevel",
    "ref",
    "gt",
    "qual",
    "filter",
    "variationId",
    "rsId",
    "omimId",
    "classification",
    "conditions",
    "clinSig",
    "reviewStatus",
    "lastEvaluated",
    "accession",
    "pubmed",
    "afAfr",
    "afEas",
    "afFin",
    "afNfe",
    "afSas",
    "afAmr",
    "af",
    "ac",
    "an",
    "siftMax",
  ])
}

#
# initQuery Lambda Function
#
module "lambda-initQuery" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-initQuery"
  description   = "Invokes queryVCF with the calculated regions"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 1792
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-initQuery.json
  }
  source_path = "${path.module}/lambda/initQuery"
  tags        = var.common-tags

  environment = {
    variables = {
      CONCAT_STARTER_SNS_TOPIC_ARN  = aws_sns_topic.concatStarter.arn
      NEXT_FUNCTION_SNS_TOPIC_ARN   = aws_sns_topic.queryVCF.arn
      RESULT_DURATION               = local.result_duration
      RESULT_SUFFIX                 = local.result_suffix
      SLICE_SIZE_MBP                = local.slice_size_mbp
      SVEP_TEMP                     = aws_s3_bucket.svep-temp.bucket
      HTS_S3_HOST                   = "s3.${var.region}.amazonaws.com"
      DYNAMO_PROJECT_USERS_TABLE    = var.dynamo-project-users-table
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
    }
  }

  layers = [
    local.binaries_layer,
    local.python_modules_layer,
  ]
}

#
# initQuery Lambda Function
#
module "lambda-sendJobEmail" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-sendJobEmail"
  description   = "Invokes sendJobEmail to send email to user"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 1792
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-sendJobEmail.json
  }
  source_path = "${path.module}/lambda/sendJobEmail"
  tags        = var.common-tags

  environment = {
    variables = {
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
    }
  }

  layers = [
    local.binaries_layer,
    local.python_modules_layer,
  ]
}

#
# queryVCF Lambda Function
#
module "lambda-queryVCF" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-queryVCF"
  description   = "Invokes queryGTF for each region."
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-queryVCF.json
  }
  source_path = "${path.module}/lambda/queryVCF"
  tags        = var.common-tags

  environment = {
    variables = {
      SVEP_TEMP                      = aws_s3_bucket.svep-temp.bucket
      NEXT_FUNCTION_SNS_TOPIC_ARN    = aws_sns_topic.queryGTF.arn
      QUERY_VCF_SUBMIT_SNS_TOPIC_ARN = aws_sns_topic.queryVCFsubmit.arn
      SLICE_SIZE_MBP                 = local.slice_size_mbp
      FILTER_MIN_QUAL                = var.filters.min_qual
      DYNAMO_CLINIC_JOBS_TABLE       = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA  = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                   = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN             = aws_sns_topic.sendJobEmail.arn
      HTS_S3_HOST                    = "s3.${var.region}.amazonaws.com"
    }
  }

  layers = [
    local.binaries_layer,
    local.python_modules_layer,
  ]
}

#
# queryVCFsubmit Lambda Function
#
module "lambda-queryVCFsubmit" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-queryVCFsubmit"
  description   = "This lambda will be called if there are too many batchids to be processed within"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-queryVCFsubmit.json
  }
  source_path = "${path.module}/lambda/queryVCFsubmit"
  tags        = var.common-tags

  environment = {
    variables = {
      SVEP_TEMP                     = aws_s3_bucket.svep-temp.bucket
      NEXT_FUNCTION_SNS_TOPIC_ARN   = aws_sns_topic.queryGTF.arn
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
    }
  }

  layers = [
    local.python_modules_layer
  ]
}

#
# queryGTF Lambda Function
#
module "lambda-queryGTF" {
  source        = "github.com/bhosking/terraform-aws-lambda"
  function_name = "svep-backend-queryGTF"
  description   = "Queries GTF for a specified VCF regions."
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 24
  policy = {
    json = data.aws_iam_policy_document.lambda-queryGTF.json
  }
  source_path = "${path.module}/lambda/queryGTF"
  tags        = var.common-tags
  environment = {
    variables = {
      REFERENCE_LOCATION            = aws_s3_bucket.svep-references.bucket
      SVEP_TEMP                     = aws_s3_bucket.svep-temp.bucket
      REFERENCE_GENOME              = "sorted_filtered_${var.gtf_file_base}.gtf.bgz"
      NEXT_FUNCTION_SNS_TOPIC_ARN   = aws_sns_topic.pluginConsequence.arn
      FILTER_GENES                  = join(",", var.filters.genes)
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
      HTS_S3_HOST                   = "s3.${var.region}.amazonaws.com"
    }
  }

  layers = [
    local.binaries_layer,
    local.python_modules_layer,
  ]
}

#
# pluginConsequence Lambda Function
#
# TODO: update source to github.com/bhosking/terraform-aws-lambda once docker support is added
module "lambda-pluginConsequence" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "svep-backend-pluginConsequence"
  description         = "Queries VCF for a specified variant."
  create_package      = false
  image_uri           = module.docker_image_pluginConsequence_lambda.image_uri
  package_type        = "Image"
  memory_size         = 2048
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-pluginConsequence.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/pluginConsequence"
  tags                   = var.common-tags
  environment_variables = {
    SVEP_TEMP                     = aws_s3_bucket.svep-temp.bucket
    SVEP_REGIONS                  = aws_s3_bucket.svep-regions.bucket
    NEXT_FUNCTION_SNS_TOPIC_ARN   = aws_sns_topic.pluginClinvar.arn
    REFERENCE_LOCATION            = aws_s3_bucket.svep-references.bucket
    SPLICE_REFERENCE              = "sorted_${var.splice_file_base}.gtf.bgz"
    MIRNA_REFERENCE               = "sorted_filtered_${var.mirna_file_base}.gff3.bgz"
    FASTA_REFERENCE_BASE          = var.fasta_file_base
    FILTER_CONSEQUENCE_RANK       = var.filters.consequence_rank
    DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
    COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
    SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
    USER_POOL_ID                  = var.cognito-user-pool-id
    HTS_S3_HOST                   = "s3.${var.region}.amazonaws.com"
  }
}

#
# pluginClinvar Lambda Function
#
module "lambda-pluginClinvar" {
  source        = "github.com/bhosking/terraform-aws-lambda"
  function_name = "svep-backend-pluginClinvar"
  description   = "Add ClinVar annotations to sVEP result rows."
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 24
  policy = {
    json = data.aws_iam_policy_document.lambda-pluginClinvar.json
  }
  source_path = "${path.module}/lambda/pluginClinvar"
  tags        = var.common-tags
  environment = {
    variables = {
      SVEP_TEMP                     = aws_s3_bucket.svep-temp.bucket
      REFERENCE_LOCATION            = aws_s3_bucket.svep-references.bucket
      CLINVAR_REFERENCE             = "clinvar.bed.gz"
      NEXT_FUNCTION_SNS_TOPIC_ARN   = aws_sns_topic.pluginGnomad.arn
      FILTER_CLINVAR_EXCLUDE        = join(",", var.filters.clinvar_exclude)
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
      HTS_S3_HOST                   = "s3.${var.region}.amazonaws.com"
    }
  }

  layers = [
    local.binaries_layer,
    local.python_modules_layer,
  ]
}

#
# pluginGnomad Lambda Function
#
module "lambda-pluginGnomad" {
  source        = "github.com/bhosking/terraform-aws-lambda"
  function_name = "svep-backend-pluginGnomad"
  description   = "Add Gnomad annotations to sVEP result rows."
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 900
  policy = {
    json = data.aws_iam_policy_document.lambda-pluginGnomad.json
  }
  source_path = "${path.module}/lambda/pluginGnomad"
  tags        = var.common-tags
  environment = {
    variables = {
      SVEP_TEMP                     = aws_s3_bucket.svep-temp.bucket
      NEXT_FUNCTION_SNS_TOPIC_ARN   = aws_sns_topic.formatOutput.arn
      FILTER_MAX_MAF                = var.filters.max_maf
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
    }
  }

  layers = [
    local.binaries_layer,
    local.python_modules_layer,
  ]
}

#
# concat Lambda Function
#
module "lambda-concat" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-concat"
  description   = "Triggers createPages."
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-concat.json
  }
  source_path = "${path.module}/lambda/concat"
  tags        = var.common-tags

  environment = {
    variables = {
      SVEP_REGIONS                  = aws_s3_bucket.svep-regions.bucket
      CREATEPAGES_SNS_TOPIC_ARN     = aws_sns_topic.createPages.arn
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
    }
  }

  layers = [
    local.python_modules_layer
  ]
}

#
# concatStarter Lambda Function
#
module "lambda-concatStarter" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-concatStarter"
  description   = "Validates all processing is done and triggers concat"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 128
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-concatStarter.json
  }
  source_path = "${path.module}/lambda/concatStarter"
  tags        = var.common-tags

  environment = {
    variables = {
      SVEP_TEMP                     = aws_s3_bucket.svep-temp.bucket
      SVEP_REGIONS                  = aws_s3_bucket.svep-regions.bucket
      CONCAT_SNS_TOPIC_ARN          = aws_sns_topic.concat.arn
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
    }
  }

  layers = [
    local.python_modules_layer,
  ]
}

#
# createPages Lambda Function
#
module "lambda-createPages" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-createPages"
  description   = "concatenates individual page with 700 entries, received from concat lambda"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-createPages.json
  }
  source_path = "${path.module}/lambda/createPages"
  tags        = var.common-tags

  environment = {
    variables = {
      SVEP_REGIONS                  = aws_s3_bucket.svep-regions.bucket
      SVEP_RESULTS                  = var.data_portal_bucket_name
      CONCATPAGES_SNS_TOPIC_ARN     = aws_sns_topic.concatPages.arn
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
    }
  }

  layers = [
    local.python_modules_layer,
  ]
}

#
# concatPages Lambda Function
#
module "lambda-concatPages" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-concatPages"
  description   = "concatenates all the page files created by createPages lambda."
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-concatPages.json
  }
  source_path = "${path.module}/lambda/concatPages"
  tags        = var.common-tags

  environment = {
    variables = {
      RESULT_SUFFIX                 = local.result_suffix
      SVEP_REGIONS                  = aws_s3_bucket.svep-regions.bucket
      SVEP_RESULTS                  = var.data_portal_bucket_name
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
    }
  }

  layers = [
    local.python_modules_layer
  ]
}

#
# getResultsURL Lambda Function
#
module "lambda-getResultsURL" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "svep-backend-getResultsURL"
  description   = "Returns the presigned results URL for results"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 1792
  timeout       = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-getResultsURL.json
  }
  source_path = "${path.module}/lambda/getResultsURL"
  tags        = var.common-tags

  environment = {
    variables = {
      REGION                     = var.region
      RESULT_DURATION            = local.result_duration
      RESULT_SUFFIX              = local.result_suffix
      SVEP_RESULTS               = var.data_portal_bucket_name
      DYNAMO_PROJECT_USERS_TABLE = var.dynamo-project-users-table
    }
  }

  layers = [
    local.python_modules_layer,
  ]
}

#
# updateReferenceFiles Lambda Function
#
module "lambda-updateReferenceFiles" {
  source = "terraform-aws-modules/lambda/aws"

  function_name          = "svep-backend-updateReferenceFiles"
  description            = "Retrieves latest reference files and updates the reference bucket in S3"
  runtime                = "python3.12"
  handler                = "lambda_function.lambda_handler"
  memory_size            = 2048
  timeout                = 900
  ephemeral_storage_size = 8192
  attach_policy_jsons    = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-updateReferenceFiles.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/updateReferenceFiles"

  tags = var.common-tags

  environment_variables = {
    REFERENCE_LOCATION                 = aws_s3_bucket.svep-references.bucket
    DYNAMO_SVEP_REFERENCES_TABLE       = aws_dynamodb_table.svep_references.name
    GTF_BASE                           = var.gtf_file_base
    SPLICE_BASE                        = var.splice_file_base
    FASTA_BASE                         = var.fasta_file_base
    MIRNA_BASE                         = var.mirna_file_base
    UPDATEREFERENCEFILES_SNS_TOPIC_ARN = aws_sns_topic.updateReferenceFiles.arn
    EC2_IAM_INSTANCE_PROFILE           = aws_iam_instance_profile.ec2_references_instance_profile.name
  }

  layers = [
    local.binaries_layer,
    local.python_modules_layer,
  ]
}

module "lambda-clearTempAndRegions" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "svep-backend-clearTempAndRegions"
  description         = "Clears temp and regions buckets for sVEP executions that fail"
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 2048
  timeout             = 600
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-clearTempAndRegions.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/clearTempAndRegions"

  tags = var.common-tags

  environment_variables = {
    SVEP_TEMP    = aws_s3_bucket.svep-temp.bucket
    SVEP_REGIONS = aws_s3_bucket.svep-regions.bucket
  }
}

#
# formatOutput Lambda Function
#
module "lambda-formatOutput" {
  source        = "github.com/bhosking/terraform-aws-lambda"
  function_name = "svep-backend-formatOutput"
  description   = "Convert input list of dictionaries to a TSV file."
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 2048
  timeout       = 24
  policy = {
    json = data.aws_iam_policy_document.lambda-formatOutput.json
  }
  source_path = "${path.module}/lambda/formatOutput"
  tags        = var.common-tags
  environment = {
    variables = {
      SVEP_TEMP                     = aws_s3_bucket.svep-temp.bucket
      SVEP_REGIONS                  = aws_s3_bucket.svep-regions.bucket
      DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
      COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
      USER_POOL_ID                  = var.cognito-user-pool-id
      SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
      COLUMNS                       = local.output_columns
    }
  }

  layers = [
    local.python_modules_layer,
  ]
}

#
# qcFigures Lambda Function
#
module "lambda-qcFigures" {
  source = "terraform-aws-modules/lambda/aws"

  function_name          = "svep-backend-qcFigures"
  description            = "Running vcfstats for generating graphic."
  create_package         = false
  image_uri              = module.docker_image_qcFigures_lambda.image_uri
  package_type           = "Image"
  memory_size            = 3000
  timeout                = 900
  ephemeral_storage_size = 10240
  attach_policy_jsons    = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-qcFigures.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/qcFigures"
  tags                   = var.common-tags
  environment_variables = {
    FILE_LOCATION   = var.data_portal_bucket_name
    USER_POOL_ID    = var.cognito-user-pool-id
    HTS_S3_HOST     = "s3.${var.region}.amazonaws.com"
    RESULT_DURATION = local.result_duration
  }
}

#
# deleteClinicalWorkflow Lambda Function
#
module "lambda-deleteClinicalWorkflow" {
  source = "terraform-aws-modules/lambda/aws"

  function_name          = "svep-backend-deleteClinicalWorkflow"
  description            = "Delete pending after 2 days clinical workflow using cron job."
  runtime                = "python3.12"
  handler                = "lambda_function.lambda_handler"
  memory_size            = 2048
  timeout                = 900
  ephemeral_storage_size = 8192
  attach_policy_jsons    = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-deleteClinicalWorkflow.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/deleteClinicalWorkflow"

  tags = var.common-tags

  environment_variables = {
    DYNAMO_CLINIC_JOBS_TABLE      = var.dynamo-clinic-jobs-table
    COGNITO_SVEP_JOB_EMAIL_LAMBDA = var.svep-job-email-lambda-function-arn
    USER_POOL_ID                  = var.cognito-user-pool-id
    SEND_JOB_EMAIL_ARN            = aws_sns_topic.sendJobEmail.arn
  }

  layers = [
    local.binaries_layer,
    local.python_modules_layer,
  ]
}
