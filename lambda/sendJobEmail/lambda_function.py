import os
import json
import boto3

from shared.dynamodb import query_clinic_job
from shared.utils.cognito_utils import get_cognito_user_by_id
from shared.utils import get_sns_event

lambda_client = boto3.client("lambda")

COGNITO_CLINIC_JOB_EMAIL_LAMBDA = os.environ.get("COGNITO_CLINIC_JOB_EMAIL_LAMBDA", "")


def lambda_handler(event, _):
    message = get_sns_event(event)

    print(f"[send_job_email] - Starting message received: {json.dumps(message)}")

    job_id = message["job_id"]
    job_status = message["job_status"]
    project_name = message.get("project_name", None)
    input_vcf = message.get("input_vcf", None)
    user_id = message.get("user_id", None)
    is_from_failed_execution = message.get("is_from_failed_execution", False)

    # prevent re querying the job if it's already queried from handle_failed_execution
    # in handle_failed_execution already queried the job using query_clinic_job
    job = (
        {
            "svep_status": {"S": job_status},
            "project_name": {"S": project_name},
            "input_vcf": {"S": input_vcf},
        }
        if is_from_failed_execution
        else query_clinic_job(job_id)
    )

    if job:
        job_status = job.get("job_status", {}).get("S", job_status)
        project_name = job.get("project_name", {}).get("S", project_name)
        input_vcf = job.get("input_vcf", {}).get("S", input_vcf)

    print(f"[send_job_email] - job result : {json.dumps(job)}")

    # handle when user_id is not provided
    # this can happen when the job is created by a lambda function initQuery
    user_id = user_id or job.get("uid", {}).get("S")

    user_info = get_cognito_user_by_id(uid=user_id)
    if not user_info:
        print(f"[send_job_email] - Skipping email for job: user not found")
        return

    print(f"[send_job_email] - user_info result : {json.dumps(user_info)}")

    payload = {
        "body": {
            "job_id": job_id,
            "email": user_info["email"],
            "first_name": user_info["first_name"],
            "last_name": user_info["last_name"],
            "job_status": job_status,
            "project_name": project_name,
            "input_vcf": input_vcf,
        }
    }

    print(f"[send_job_email] - payload: {payload}")

    response = lambda_client.invoke(
        FunctionName=COGNITO_CLINIC_JOB_EMAIL_LAMBDA,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    if not (payload_stream := response.get("Payload")):
        raise Exception("Error invoking email Lambda: No response payload")
    body = json.loads(payload_stream.read().decode("utf-8"))
    if not body.get("success", False):
        raise Exception(f"Error invoking email Lambda: {body.get('message')}")

    email_sent = body.get("success", False)

    print(f"[send_job_email] Email sent: {email_sent}")
