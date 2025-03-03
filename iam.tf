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
    ]
  }

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
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.svep-temp.arn}/*",
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
      aws_sns_topic.pluginUpdownstream.arn,
      aws_sns_topic.queryGTF.arn,
    ]
  }

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
}

#
# pluginUpdownstream Lambda Function
#
data "aws_iam_policy_document" "lambda-pluginUpdownstream" {
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
}

#
# pluginClinvar Lambda Function
#
data "aws_iam_policy_document" "lambda-pluginClinvar" {
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
}
