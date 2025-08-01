#
# Cloudwatch trigger for updating references
#
resource "aws_cloudwatch_event_rule" "update_references_trigger" {
  name                = "svep_update_references_trigger"
  description         = "A scheduled trigger that checks for changes to and updates reference files used by sVEP."
  schedule_expression = "rate(1 day)"
}

resource "aws_cloudwatch_event_target" "update_references_trigger" {
  rule      = aws_cloudwatch_event_rule.update_references_trigger.name
  target_id = "lambda-updateReferenceFiles"
  arn       = module.lambda-updateReferenceFiles.lambda_function_arn
}


#
# Cloudwatch trigger for deleting pending after 2 days jobs clinical workflows 
#
resource "aws_cloudwatch_event_rule" "delete_clinical_trigger" {
  name                = "svep_delete_clinical_trigger"
  description         = "A scheduled trigger that checks for pending jobs in clinical workflows and deletes them."
  schedule_expression = "cron(0 16 * * ? *)"
}

resource "aws_cloudwatch_event_target" "delete_clinical_trigger" {
  rule      = aws_cloudwatch_event_rule.delete_clinical_trigger.name
  target_id = "lambda-deleteClinicalWorkflow"
  arn       = module.lambda-deleteClinicalWorkflow.lambda_function_arn
}

#
# Cloudwatch trigger for batch job starter
#
resource "aws_cloudwatch_event_rule" "batch_starter_trigger" {
  name                = "svep-backend-batchStarterTrigger"
  description         = "Trigger for initiation of queued batch job submissions."
  schedule_expression = "rate(2 minutes)"
}

resource "aws_cloudwatch_event_target" "batch_starter_trigger" {
  rule      = aws_cloudwatch_event_rule.batch_starter_trigger.name
  target_id = "lambda-batchStarter"
  arn       = module.lambda-batchStarter.lambda_function_arn
}
