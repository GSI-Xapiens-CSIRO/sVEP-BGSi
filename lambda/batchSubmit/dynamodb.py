import os

from shared.utils import LoggingClient

dynamodb_client = LoggingClient("dynamodb")

DYNAMO_PROJECT_USERS_TABLE = os.environ["DYNAMO_PROJECT_USERS_TABLE"]
DYNAMO_CLINIC_JOBS_TABLE = os.environ["DYNAMO_CLINIC_JOBS_TABLE"]
JOBS_TABLE_PROJECT_NAME_INDEX = os.environ["CLINIC_JOBS_TABLE_PROJECT_NAME_INDEX"]


def batch_check_duplicate_job_name(job_names, project_name):
    job_names_lower = [name.lower() for name in job_names]

    # Check for duplicates within the submission
    batch_duplicates = {
        name for name in job_names_lower if job_names_lower.count(name) > 1
    }
    if batch_duplicates:
        return batch_duplicates

    # Check for duplicates that already exist in DynamoDB
    paginator = dynamodb_client.get_paginator("query")
    page_iterator = paginator.paginate(
        TableName=DYNAMO_CLINIC_JOBS_TABLE,
        IndexName=JOBS_TABLE_PROJECT_NAME_INDEX,
        KeyConditionExpression="project_name = :project",
        ExpressionAttributeValues={":project": {"S": project_name}},
        ProjectionExpression="job_name_lower",
    )

    existing_job_names = set()
    for page in page_iterator:
        for item in page["Items"]:
            if not item:
                continue
            existing_job_names.add(item["job_name_lower"]["S"])

    existing_duplicates = set(job_names_lower).intersection(existing_job_names)

    if existing_duplicates:
        return existing_duplicates

    return set()
