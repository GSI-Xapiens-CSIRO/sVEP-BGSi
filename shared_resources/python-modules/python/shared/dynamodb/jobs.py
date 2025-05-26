import boto3
import os
import json
from datetime import datetime, timedelta, timezone

dynamodb_client = boto3.client("dynamodb")

lambda_client = boto3.client("lambda")
dynamodb_client = boto3.client("dynamodb")
sns = boto3.client("sns")

DYNAMO_CLINIC_JOBS_TABLE = os.environ.get("DYNAMO_CLINIC_JOBS_TABLE", "")
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


def scan_pending_jobs():
    # Get timestamp 2 days ago in ISO 8601 format
    threshold_time = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    print(f"[scan_pending_jobs] - Threshold timestamp: {threshold_time}")

    all_items = []
    last_evaluated_key = None

    while True:
        scan_kwargs = {
            "TableName": DYNAMO_CLINIC_JOBS_TABLE,
            "FilterExpression": "job_status = :status AND created_at < :threshold",
            "ExpressionAttributeValues": {
                ":status": {"S": "pending"},
                ":threshold": {"S": threshold_time},
            },
        }

        if last_evaluated_key:
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        response = dynamodb_client.scan(**scan_kwargs)
        items = response.get("Items", [])
        all_items.extend(items)

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

    print(f"[scan_pending_jobs] - Found {len(all_items)} old pending jobs.")
    print(f"[scan_pending_jobs] - Items: {all_items}")
    return all_items


def bulk_delete_jobs(items):
    table_name = DYNAMO_CLINIC_JOBS_TABLE
    # DynamoDB batch write item can only handle 25 items at a time
    chunks = [items[i : i + 25] for i in range(0, len(items), 25)]

    for chunk in chunks:
        delete_requests = [
            {
                "DeleteRequest": {
                    "Key": {"job_id": item["job_id"]}  # Include sort key too if needed
                }
            }
            for item in chunk
        ]

        response = dynamodb_client.batch_write_item(
            RequestItems={table_name: delete_requests}
        )
        unprocessed = response.get("UnprocessedItems", {})
        if unprocessed:
            print("⚠️ Unprocessed items:", unprocessed)


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
    }

    if project_name is not None:
        update_fields["project_name"] = {"S": project_name}
    if job_name is not None:
        update_fields["job_name"] = {"S": job_name}
        update_fields["job_name_lower"] = {"S": job_name.lower()}
        # Added created_at at the first time a job is created
        now = datetime.now(timezone.utc)
        update_fields["created_at"] = {"S": now.isoformat()}
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

    if job_status == "pending":
        print(f"[update_clinic_job] - Skipping email for job status: {job_status}")
        return

    send_job_email(
        job_id=job_id,
        job_status=job_status,
        project_name=project_name,
        input_vcf=input_vcf,
        user_id=user_id,
        is_from_failed_execution=is_from_failed_execution,
    )
