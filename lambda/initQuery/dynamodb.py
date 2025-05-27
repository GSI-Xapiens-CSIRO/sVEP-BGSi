import boto3
import os

dynamodb_client = boto3.client("dynamodb")

DYNAMO_PROJECT_USERS_TABLE = os.environ["DYNAMO_PROJECT_USERS_TABLE"]
DYNAMO_CLINIC_JOBS_TABLE = os.environ.get("DYNAMO_CLINIC_JOBS_TABLE", "")
JOBS_TABLE_PROJECT_NAME_INDEX = os.environ["CLINIC_JOBS_PROJECT_NAME_INDEX"]


def check_user_in_project(sub, project):
    # check user in project
    response = dynamodb_client.get_item(
        TableName=DYNAMO_PROJECT_USERS_TABLE,
        Key={"name": {"S": project}, "uid": {"S": sub}},
    )

    assert "Item" in response, "User not found in project"


def does_clinic_job_exist_by_name(job_name_lower, project_name):
    project_name = project_name.strip()
    job_name_lower = job_name_lower.strip()

    response = dynamodb_client.query(
        TableName=DYNAMO_CLINIC_JOBS_TABLE,
        IndexName=JOBS_TABLE_PROJECT_NAME_INDEX,
        KeyConditionExpression="project_name = :project",
        FilterExpression="job_name_lower = :job",
        ExpressionAttributeValues={
            ":project": {"S": project_name},
            ":job": {"S": job_name_lower},
        },
    )

    print(
        f"[DEBUG] Cleaned Params: project_name='{project_name}', job_name_lower='{job_name_lower}'"
    )
    print(f"[DEBUG] Query result count: {response.get('Count', 0)}")
    print(f"[DEBUG] Full response: {json.dumps(response, default=str)}")

    return response.get("Count", 0) > 0
