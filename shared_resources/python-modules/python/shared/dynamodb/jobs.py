import json
import os

import boto3
from botocore.exceptions import ClientError

lambda_client = boto3.client("lambda")
dynamodb_client = boto3.client("dynamodb")

DYNAMO_CLINIC_JOBS_TABLE = os.environ.get("DYNAMO_CLINIC_JOBS_TABLE", "")
DYNAMO_PROJECT_USERS_TABLE = os.environ.get("DYNAMO_PROJECT_USERS_TABLE", "")
COGNITO_SVEP_JOB_EMAIL_LAMBDA = os.environ.get("COGNITO_SVEP_JOB_EMAIL_LAMBDA", "")
USER_POOL_ID = os.environ.get("USER_POOL_ID", "")

cognito_client = boto3.client("cognito-idp")


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


def get_cognito_user(user_id: str):
    cognito_client = boto3.client("cognito-idp")

    try:
        response = cognito_client.admin_get_user(
            UserPoolId=USER_POOL_ID, Username=user_id  # Use Cognito User ID (sub)
        )

        # Extract attributes
        attributes = {
            attr["Name"]: attr["Value"] for attr in response["UserAttributes"]
        }

        return {
            "email": attributes.get("email", ""),
            "first_name": attributes.get("given_name", ""),
            "last_name": attributes.get("family_name", ""),
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "UserNotFoundException":
            print("User not found.")
        else:
            print(f"An error occurred: {e.response['Error']['Message']}")
        return None  # Return None when user is not found or an error occurs


def send_job_email(
    job_status,
    project_name=None,
    input_vcf=None,
    user_id=None,
):
    if (job_status == "pending") or (job_status == "expired"):
        print(f"Skipping email for job status: {job_status}")
        return

    user_info = get_cognito_user(USER_POOL_ID, user_id)

    if not user_info:
        print(f"Skipping email, user not found")
        return

    payload = {
        "body": {
            "email": "fajarsep12@gmail.com",
            "first_name": user_info["first_name"],
            "last_name": user_info["last_name"],
            "job_status": job_status,
            "project_name": project_name,
            "input_vcf": input_vcf,
        }
    }

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

    print(f"Email sent: {email_sent}")


def update_clinic_job(
    job_id,
    job_status,
    project_name=None,
    input_vcf=None,
    failed_step=None,
    error_message=None,
    user_id=None,
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


def check_user_in_project(sub, project):
    response = dynamodb_client.get_item(
        TableName=DYNAMO_PROJECT_USERS_TABLE,
        Key={"name": {"S": project}, "uid": {"S": sub}},
    )

    assert "Item" in response, "User not found in project"
