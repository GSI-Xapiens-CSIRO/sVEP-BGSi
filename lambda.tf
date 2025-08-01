#
# initQuery Lambda Function
#
resource "aws_lambda_permission" "init_query_invoke_permission" {
  statement_id  = "APIInitQueryAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-initQuery.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.VPApi.execution_arn}/*/*/${aws_api_gateway_resource.submit.path_part}"
}
resource "aws_lambda_function_recursion_config" "init_query_recursion" {
  function_name  = module.lambda-initQuery.function_name
  recursive_loop = "Allow"
}

resource "aws_lambda_permission" "initquery_invoke_permission_sns" {
  statement_id  = "SNSInitQueryAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-initQuery.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.initQuery.arn
}

#
# getResults Lambda Function
#
resource "aws_lambda_permission" "get_results_invoke_permission" {
  statement_id  = "APIGetResultsAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getResultsURL.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.VPApi.execution_arn}/*/*/${aws_api_gateway_resource.results.path_part}"
}

#
# batchSubmit Lambda Function
#
resource "aws_lambda_permission" "batch_submit_invoke_permission" {
  statement_id  = "APIBatchSubmitAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-batchSubmit.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.VPApi.execution_arn}/*/*/${aws_api_gateway_resource.batch-submit.path_part}"
}

#
# queryVCF Lambda Function
#
resource "aws_lambda_permission" "query_vcf_invoke_permission" {
  statement_id  = "SNSQueryVCFAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-queryVCF.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.queryVCF.arn
}
resource "aws_lambda_function_recursion_config" "query_vcf_recursion" {
  function_name  = module.lambda-queryVCF.function_name
  recursive_loop = "Allow"
}

#
# queryVCFsubmit Lambda Function
#
resource "aws_lambda_permission" "query_vcf_submit_invoke_permission" {
  statement_id  = "SNSQueryVCFSubmitAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-queryVCFsubmit.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.queryVCFsubmit.arn
}

#
# queryGTF Lambda Function
#
resource "aws_lambda_permission" "query_gtf_invoke_permission" {
  statement_id  = "SNSQueryGTFAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-queryGTF.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.queryGTF.arn
}
resource "aws_lambda_function_recursion_config" "query_gtf_recursion" {
  function_name  = module.lambda-queryGTF.function_name
  recursive_loop = "Allow"
}


#
# pluginConsequence Lambda Function
#
resource "aws_lambda_permission" "plugin_consequence_invoke_permission" {
  statement_id  = "SNSPluginConsequenceAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-pluginConsequence.lambda_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.pluginConsequence.arn
}
resource "aws_lambda_function_recursion_config" "plugin_consequence_recursion" {
  function_name  = module.lambda-pluginConsequence.lambda_function_name
  recursive_loop = "Allow"
}


#
# pluginClinvar Lambda Function
#
resource "aws_lambda_permission" "plugin_clinvar_invoke_permission" {
  statement_id  = "SNSPluginClinvarAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-pluginClinvar.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.pluginClinvar.arn
}


#
# concat Lambda Function
#
resource "aws_lambda_permission" "concat_invoke_permission" {
  statement_id  = "SNSConcatAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-concat.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.concat.arn
}

#
# concatStarter Lambda Function
#
resource "aws_lambda_permission" "concat_starter_invoke_permission" {
  statement_id  = "SNSConcatStarterAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-concatStarter.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.concatStarter.arn
}
resource "aws_lambda_function_recursion_config" "concat_starter_recursion" {
  function_name  = module.lambda-concatStarter.function_name
  recursive_loop = "Allow"
}

#
# createPages Lambda Function
#
resource "aws_lambda_permission" "create_pages_invoke_permission" {
  statement_id  = "SNSCreatePagesAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-createPages.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.createPages.arn
}
resource "aws_lambda_function_recursion_config" "create_pages_recursion" {
  function_name  = module.lambda-createPages.function_name
  recursive_loop = "Allow"
}

#
# concatPages Lambda Function
#
resource "aws_lambda_permission" "concat_pages_invoke_permission" {
  statement_id  = "SNSConcatPagesAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-concatPages.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.concatPages.arn
}

#
# updateReferenceFiles Lambda Function
#
resource "aws_lambda_permission" "sns_update_reference_files_invoke_permission" {
  statement_id  = "SNSUpdateReferenceFilesAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-updateReferenceFiles.lambda_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.updateReferenceFiles.arn
}

resource "aws_lambda_permission" "cloudwatch_update_reference_files_invoke_permission" {
  statement_id  = "CloudwatchUpdateReferenceFilesAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-updateReferenceFiles.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.update_references_trigger.arn
}

resource "aws_lambda_function_recursion_config" "update_reference_files_recursion" {
  function_name  = module.lambda-updateReferenceFiles.lambda_function_name
  recursive_loop = "Allow"
}

#
# clearTempAndRegions Lambda Function
#
resource "aws_lambda_event_source_mapping" "clinic_jobs_stream_event_source" {
  event_source_arn  = var.dynamo-clinic-jobs-stream-arn
  function_name     = module.lambda-clearTempAndRegions.lambda_function_name
  starting_position = "LATEST"

  filter_criteria {
    filter {
      pattern = jsonencode({
        eventName = ["MODIFY"]
      })
    }
  }
}

resource "aws_lambda_permission" "clearTempAndRegions_invoke_permission" {
  statement_id  = "SNSclearTempAndRegionsAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-clearTempAndRegions.lambda_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.clearTempAndRegions.arn
}

#
# sendJobEmail Lambda Function
#
resource "aws_lambda_permission" "plugin_send_job_email_invoke_permission" {
  statement_id  = "SNSSendJobEmailAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-sendJobEmail.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.sendJobEmail.arn
}

#
# pluginGnomad Lambda Function
#
resource "aws_lambda_permission" "plugin_plugin_gnomad_invoke_permission" {
  statement_id  = "SNSPluginGnomadAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-pluginGnomad.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.pluginGnomad.arn

}
#
# pluginGnomadOneKG Lambda Function
#
resource "aws_lambda_permission" "plugin_plugin_gnomad_one_kg_invoke_permission" {
  statement_id  = "SNSPluginGnomadAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-pluginGnomadOneKG.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.pluginGnomadOneKG.arn

}
#
# pluginGnomadConstraint Lambda Function
#
resource "aws_lambda_permission" "plugin_plugin_gnomad_constraint_invoke_permission" {
  statement_id  = "SNSPluginGnomadAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-pluginGnomadConstraint.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.pluginGnomadConstraint.arn

}

#
# formatOutput Lambda Function
#
resource "aws_lambda_permission" "formatOutput_invoke_permission" {
  statement_id  = "SNSformatOutputAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-formatOutput.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.formatOutput.arn
}

#
# vcfstatsGraphic Lambda Function
#
resource "aws_lambda_permission" "vcfstats_graphic_invoke_permission" {
  statement_id  = "APIVcfstatsAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-qcFigures.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.VPApi.execution_arn}/*/*/${aws_api_gateway_resource.vcfstats.path_part}"
}

#
# qcNotes Lambda Function
#
resource "aws_lambda_permission" "qcNotes_invoke_permission" {
  statement_id  = "SvepAPIQcNotesAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-qcNotes.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.VPApi.execution_arn}/*/*/${aws_api_gateway_resource.qcnotes.path_part}"
}

#
# updateReferenceFiles Lambda Function
#
resource "aws_lambda_permission" "cloudwatch_svep_reference_update_permission" {
  statement_id  = "CloudwatchSvepReferenceUpdateAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-updateReferenceFiles.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.update_references_trigger.arn
}

#
# deleteClinicalWorkflow Lambda Function
#
resource "aws_lambda_permission" "cloudwatch_delete_clinical_workflow_invoke_permission" {
  statement_id  = "CloudwatchDeleteClinicalWorkflowAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-deleteClinicalWorkflow.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.delete_clinical_trigger.arn
}

#
# batchStarter Lambda Function
#
resource "aws_lambda_permission" "cloudwatch_batch_starter_invoke_permission" {
  statement_id  = "CloudwatchBatchStarterAllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-batchStarter.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.batch_starter_trigger.arn
}
