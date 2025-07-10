resource "aws_sns_topic" "queryVCF" {
  name = "svep-backend-queryVCF"
}

resource "aws_sns_topic_subscription" "queryVCF" {
  topic_arn = aws_sns_topic.queryVCF.arn
  protocol  = "lambda"
  endpoint  = module.lambda-queryVCF.function_arn
}
resource "aws_sns_topic" "queryVCFsubmit" {
  name = "svep-backend-queryVCFsubmit"
}

resource "aws_sns_topic_subscription" "queryVCFsubmit" {
  topic_arn = aws_sns_topic.queryVCFsubmit.arn
  protocol  = "lambda"
  endpoint  = module.lambda-queryVCFsubmit.function_arn
}

resource "aws_sns_topic" "queryGTF" {
  name = "svep-backend-queryGTF"
}

resource "aws_sns_topic_subscription" "queryGTF" {
  topic_arn = aws_sns_topic.queryGTF.arn
  protocol  = "lambda"
  endpoint  = module.lambda-queryGTF.function_arn
}

resource "aws_sns_topic" "pluginConsequence" {
  name = "svep-backend-pluginConsequence"
}

resource "aws_sns_topic_subscription" "pluginConsequence" {
  topic_arn = aws_sns_topic.pluginConsequence.arn
  protocol  = "lambda"
  # TODO: Reference function_arn once the module source is updated
  endpoint = module.lambda-pluginConsequence.lambda_function_arn
}

resource "aws_sns_topic" "pluginClinvar" {
  name = "svep-backend-pluginClinvar"
}

resource "aws_sns_topic_subscription" "pluginClinvar" {
  topic_arn = aws_sns_topic.pluginClinvar.arn
  protocol  = "lambda"
  endpoint  = module.lambda-pluginClinvar.function_arn
}

resource "aws_sns_topic" "pluginGnomad" {
  name = "svep-backend-pluginGnomad"
}

resource "aws_sns_topic_subscription" "pluginGnomad" {
  topic_arn = aws_sns_topic.pluginGnomad.arn
  protocol  = "lambda"
  endpoint  = module.lambda-pluginGnomad.function_arn
}

resource "aws_sns_topic" "pluginGnomadOneKG" {
  name = "svep-backend-pluginGnomadOneKG"
}

resource "aws_sns_topic_subscription" "pluginGnomadOneKG" {
  topic_arn = aws_sns_topic.pluginGnomadOneKG.arn
  protocol  = "lambda"
  endpoint  = module.lambda-pluginGnomadOneKG.function_arn
}

resource "aws_sns_topic" "pluginGnomadConstraint" {
  name = "svep-backend-pluginGnomadConstraint"
}

resource "aws_sns_topic_subscription" "pluginGnomadConstraint" {
  topic_arn = aws_sns_topic.pluginGnomadConstraint.arn
  protocol  = "lambda"
  endpoint  = module.lambda-pluginGnomadConstraint.function_arn
}

resource "aws_sns_topic" "concat" {
  name = "svep-backend-concat"
}

resource "aws_sns_topic_subscription" "concat" {
  topic_arn = aws_sns_topic.concat.arn
  protocol  = "lambda"
  endpoint  = module.lambda-concat.function_arn
}

resource "aws_sns_topic" "concatStarter" {
  name = "svep-backend-concatStarter"
}

resource "aws_sns_topic_subscription" "concatStarter" {
  topic_arn = aws_sns_topic.concatStarter.arn
  protocol  = "lambda"
  endpoint  = module.lambda-concatStarter.function_arn
}

resource "aws_sns_topic" "createPages" {
  name = "svep-backend-createPages"
}

resource "aws_sns_topic_subscription" "createPages" {
  topic_arn = aws_sns_topic.createPages.arn
  protocol  = "lambda"
  endpoint  = module.lambda-createPages.function_arn
}

resource "aws_sns_topic" "concatPages" {
  name = "svep-backend-concatPages"
}

resource "aws_sns_topic_subscription" "concatPages" {
  topic_arn = aws_sns_topic.concatPages.arn
  protocol  = "lambda"
  endpoint  = module.lambda-concatPages.function_arn
}

resource "aws_sns_topic" "updateReferenceFiles" {
  name = "svep-backend-updateReferenceFiles"
}

resource "aws_sns_topic_subscription" "updateReferenceFiles" {
  topic_arn = aws_sns_topic.updateReferenceFiles.arn
  protocol  = "lambda"
  endpoint  = module.lambda-updateReferenceFiles.lambda_function_arn
}

resource "aws_sns_topic" "sendJobEmail" {
  name = "svep-backend-sendJobEmail"
}

resource "aws_sns_topic_subscription" "sendJobEmail" {
  topic_arn = aws_sns_topic.sendJobEmail.arn
  protocol  = "lambda"
  endpoint  = module.lambda-sendJobEmail.function_arn
}

resource "aws_sns_topic" "formatOutput" {
  name = "svep-backend-formatOutput"
}

resource "aws_sns_topic_subscription" "formatOutput" {
  topic_arn = aws_sns_topic.formatOutput.arn
  protocol  = "lambda"
  endpoint  = module.lambda-formatOutput.function_arn
}

resource "aws_sns_topic" "clearTempAndRegions" {
  name = "svep-backend-clearTempAndRegions"
}

resource "aws_sns_topic_subscription" "clearTempAndRegions" {
  topic_arn = aws_sns_topic.clearTempAndRegions.arn
  protocol  = "lambda"
  endpoint  = module.lambda-clearTempAndRegions.lambda_function_arn
}
