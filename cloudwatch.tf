#
# Cloudwatch trigger for updating references
#
resource "aws_cloudwatch_event_rule" "update_references_trigger" {
    name        = "svep_update_references_trigger"
    description = "A scheduled trigger that checks for changes to and updates reference files used by sVEP."
    schedule_expression = "cron(0 19 1,15 * ? *)"
}

resource "aws_cloudwatch_event_target" "update_references_trigger" {
    rule      = aws_cloudwatch_event_rule.update_references_trigger.name
    target_id = "lambda-updateReferenceFiles"
    arn       = module.lambda-updateReferenceFiles.lambda_function_arn
}
