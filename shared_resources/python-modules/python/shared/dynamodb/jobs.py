import json
import os

import boto3

lambda_client = boto3.client("lambda")
dynamodb_client = boto3.client("dynamodb")
sns = boto3.client("sns")

DYNAMO_CLINIC_JOBS_TABLE = os.environ.get("DYNAMO_CLINIC_JOBS_TABLE", "")
DYNAMO_PROJECT_USERS_TABLE = os.environ.get("DYNAMO_PROJECT_USERS_TABLE", "")
SEND_JOB_EMAIL_ARN = os.environ.get("SEND_JOB_EMAIL_ARN", "")


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
    payload = {
        "job_id": job_id,
        "job_status": job_status,
        "project_name": project_name,
        "input_vcf": input_vcf,
        "user_id": user_id,
        "is_from_failed_execution": is_from_failed_execution,
    }

    print(f"[send_job_email] - payload: {payload}")

    kwargs = {
        "TopicArn": SEND_JOB_EMAIL_ARN,
        "Message": json.dumps(payload, separators=(",", ":")),
    }

    sns.publish(**kwargs)


def update_clinic_job(
    job_id,
    job_status,
    job_name=None,
    project_name=None,
    input_vcf=None,
    failed_step=None,
    error_message=None,
    user_id=None,
    is_from_failed_execution=False,
    skip_email=False,
):
    job_status = job_status if job_status is not None else "unknown"
    update_fields = {
        "job_status": {"S": job_status},
        "job_name": {"S": job_name},
        "job_name_lower": {
            "S": job_name.lower()
        },  # Ensure job_name is always lowercase for consistent querying
    }

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

    if skip_email:
        print(f"[update_clinic_job] - Skipping email for job: {job_id}")

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
