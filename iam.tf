#
# Generic policy documents
#
data "aws_iam_policy_document" "main-apigateway" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

# TODO: Restrict the resources on these policies
#
# initQuery Lambda Function
#
data "aws_iam_policy_document" "lambda-initQuery" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.concatStarter.arn,
      aws_sns_topic.queryVCF.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${var.data_portal_bucket_arn}/projects/*/project-files/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${var.data_portal_bucket_arn}",
    ]
  }

  statement {
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:BatchGetItem",
    ]
    resources = [
      var.dynamo-project-users-table-arn,
      var.dynamo-clinic-jobs-table-arn,
      "${var.dynamo-clinic-jobs-table-arn}/index/${local.clinic_jobs_project_name_index}",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# queryVCF Lambda Function
#
data "aws_iam_policy_document" "lambda-queryVCF" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.queryGTF.arn,
      aws_sns_topic.queryVCF.arn,
      aws_sns_topic.queryVCFsubmit.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${var.data_portal_bucket_arn}/projects/*/project-files/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${var.data_portal_bucket_arn}",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# queryVCFsubmit Lambda Function
#
data "aws_iam_policy_document" "lambda-queryVCFsubmit" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.queryGTF.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}


#
# queryGTF Lambda Function
#
data "aws_iam_policy_document" "lambda-queryGTF" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.pluginConsequence.arn,
      aws_sns_topic.queryGTF.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# pluginConsequence Lambda Function
#
data "aws_iam_policy_document" "lambda-pluginConsequence" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.pluginClinvar.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-regions.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# pluginClinvar Lambda Function
#
data "aws_iam_policy_document" "lambda-pluginClinvar" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.sendJobEmail.arn,
      aws_sns_topic.pluginGnomad.arn
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# pluginGnomad Lambda Function
#
data "aws_iam_policy_document" "lambda-pluginGnomad" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.pluginGnomad.arn,
      aws_sns_topic.sendJobEmail.arn,
      aws_sns_topic.pluginGnomadOneKG.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# pluginGnomadOneKG Lambda Function
#
data "aws_iam_policy_document" "lambda-pluginGnomadOneKG" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.pluginGnomadConstraint.arn,
      aws_sns_topic.pluginGnomadOneKG.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# pluginGnomadConstraint Lambda Function
#
data "aws_iam_policy_document" "lambda-pluginGnomadConstraint" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.pluginGnomadConstraint.arn,
      aws_sns_topic.sendJobEmail.arn,
      aws_sns_topic.formatOutput.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# concat Lambda Function
#
data "aws_iam_policy_document" "lambda-concat" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.createPages.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.svep-regions.arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-regions.arn}/*",
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# concatStarter Lambda Function
#
data "aws_iam_policy_document" "lambda-concatStarter" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.concat.arn,
      aws_sns_topic.concatStarter.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.svep-regions.arn,
      aws_s3_bucket.svep-temp.arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-regions.arn}/*",
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# createPages Lambda Function
#
data "aws_iam_policy_document" "lambda-createPages" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.concatPages.arn,
      aws_sns_topic.createPages.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-regions.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-regions.arn}/*",
      "${var.data_portal_bucket_arn}/projects/*/clinical-workflows/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.svep-regions.arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# concatPages Lambda Function
#
data "aws_iam_policy_document" "lambda-concatPages" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.concatPages.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-regions.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${var.data_portal_bucket_arn}/projects/*/clinical-workflows/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.svep-regions.arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# getResultsURL Lambda Function
#
data "aws_iam_policy_document" "lambda-getResultsURL" {
  statement {
    actions = [
      "s3:GetObject",
    ]
    resources = [
      "${var.data_portal_bucket_arn}/projects/*/clinical-workflows/*"
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      var.data_portal_bucket_arn
    ]
  }

  statement {
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:BatchGetItem",
    ]
    resources = [
      var.dynamo-project-users-table-arn,
    ]
  }
}

#
# updateReferenceFiles Lambda Function
#
data "aws_iam_policy_document" "lambda-updateReferenceFiles" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.svep-references.arn,
    ]
  }

  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.updateReferenceFiles.arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DescribeTable",
    ]
    resources = [
      aws_dynamodb_table.svep_references.arn,
    ]
  }
  statement {
    actions = [
      "ec2:RunInstances",
      "ec2:DescribeInstances",
      "ec2:CreateTags",
      "ec2:DescribeImages",
    ]
    resources = [
      "*"
    ]
  }

  statement {
    actions = [
      "iam:PassRole",
    ]
    resources = [
      aws_iam_role.ec2_references_instance_role.arn,
    ]
  }
}

#
# references EC2 Instance role - used by updateReferenceFiles
#
resource "aws_iam_instance_profile" "ec2_references_instance_profile" {
  name = "svep_backend_ec2_references_instance_profile"
  role = aws_iam_role.ec2_references_instance_role.name
}

resource "aws_iam_role" "ec2_references_instance_role" {
  name               = "svep_backend_ec2_references_instance_role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role_policy.json
}

data "aws_iam_policy_document" "ec2_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "ec2_references_policy" {
  name   = "svep_backend_ec2_references_policy"
  role   = aws_iam_role.ec2_references_instance_role.id
  policy = data.aws_iam_policy_document.ec2_references_policy.json
}

data "aws_iam_policy_document" "ec2_references_policy" {
  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }
  statement {
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.svep_references.arn,
    ]
  }
}

#
# clearTempAndRegions Lambda Function
#
data "aws_iam_policy_document" "lambda-clearTempAndRegions" {
  statement {
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.svep-temp.arn,
      aws_s3_bucket.svep-regions.arn,
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:DeleteObject"
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
      "${aws_s3_bucket.svep-regions.arn}/*"
    ]
  }

  statement {
    actions = [
      "dynamodb:GetRecords",
      "dynamodb:GetShardIterator",
      "dynamodb:DescribeStream",
      "dynamodb:ListStreams",
    ]
    resources = [
      var.dynamo-clinic-jobs-stream-arn,
    ]
  }
}

#
# initQuery Lambda Function
#
data "aws_iam_policy_document" "lambda-sendJobEmail" {
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}

#
# formatOutput Lambda Function
#
data "aws_iam_policy_document" "lambda-formatOutput" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-regions.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

  statement {
    actions = [
      "cognito-idp:ListUsers",
    ]
    resources = [
      var.cognito-user-pool-arn,
    ]
  }
}


#
# vcfstatsGraphic Lambda Function
#
data "aws_iam_policy_document" "lambda-qcFigures" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-references.arn}/*",
    ]
  }

  statement {
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${var.data_portal_bucket_arn}",
      "${var.data_portal_bucket_arn}/*",
    ]
  }
}

#
# deleteClinicalWorkflow Lambda Function
#
data "aws_iam_policy_document" "lambda-deleteClinicalWorkflow" {
  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.sendJobEmail.arn,
    ]
  }

  statement {
    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.svep-temp.arn,
    ]
  }

  statement {
    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
    ]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Scan",
      "dynamodb:BatchWriteItem"
    ]
    resources = [
      var.dynamo-clinic-jobs-table-arn,
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      var.svep-job-email-lambda-function-arn,
    ]
  }

}
