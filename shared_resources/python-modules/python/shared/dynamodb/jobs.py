import json
import os

import boto3
from shared.utils.cognito_utils import get_cognito_user_by_id

lambda_client = boto3.client("lambda")
dynamodb_client = boto3.client("dynamodb")

DYNAMO_CLINIC_JOBS_TABLE = os.environ.get("DYNAMO_CLINIC_JOBS_TABLE", "")
DYNAMO_PROJECT_USERS_TABLE = os.environ.get("DYNAMO_PROJECT_USERS_TABLE", "")
COGNITO_SVEP_JOB_EMAIL_LAMBDA = os.environ.get("COGNITO_SVEP_JOB_EMAIL_LAMBDA", "")


def query_clinic_job(job_id):
    kwargs = {
        "TableName": DYNAMO_CLINIC_JOBS_TABLE,
        "Key": {"job_id": {"S": job_id}},
    }
    print(f"Calling dynamodb.get_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb_client.get_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")
    return response.get("Item")


def dynamodb_update_item(job_id, update_fields: dict):
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in update_fields.keys())
    kwargs = {
        "TableName": DYNAMO_CLINIC_JOBS_TABLE,
        "Key": {
            "job_id": {"S": job_id},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": {f":{k}": v for k, v in update_fields.items()},
    }
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb_client.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def send_job_email(
    job_id,
    job_status,
    project_name=None,
    input_vcf=None,
    user_id=None,
    is_from_failed_execution=False,
):
    print(f"[send_job_email] - Starting : {job_id}")
    if (job_status == "pending") or (job_status == "expired"):
        print(f"Skipping email for job status: {job_status}")
        return

    # prevent re querying the job if it's already queried from handle_failed_execution
    # in handle_failed_execution already queried the job using query_clinic_job
    job = {} if is_from_failed_execution else query_clinic_job(job_id)

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
        FunctionName=COGNITO_SVEP_JOB_EMAIL_LAMBDA,
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


def update_clinic_job(
    job_id,
    job_status,
    project_name=None,
    input_vcf=None,
    failed_step=None,
    error_message=None,
    user_id=None,
    is_from_failed_execution=False,
):
    job_status = job_status if job_status is not None else "unknown"
    update_fields = {"job_status": {"S": job_status}}
    if project_name is not None:
        update_fields["project_name"] = {"S": project_name}
    if input_vcf is not None:
        update_fields["input_vcf"] = {"S": input_vcf}
    if failed_step is not None:
        update_fields["failed_step"] = {"S": failed_step}
    if error_message is not None:
        update_fields["error_message"] = {"S": error_message}
    if user_id is not None:
        update_fields["uid"] = {"S": user_id}

    dynamodb_update_item(job_id, update_fields)

    send_job_email(
        job_id=job_id,
        job_status=job_status,
        project_name=project_name,
        input_vcf=input_vcf,
        user_id=user_id,
        is_from_failed_execution=is_from_failed_execution,
    )


def check_user_in_project(sub, project):
    response = dynamodb_client.get_item(
        TableName=DYNAMO_PROJECT_USERS_TABLE,
        Key={"name": {"S": project}, "uid": {"S": sub}},
    )

    assert "Item" in response, "User not found in project"
