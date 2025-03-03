import boto3
import os

dynamodb_client = boto3.client("dynamodb")
DYNAMO_PROJECT_USERS_TABLE = os.environ["DYNAMO_PROJECT_USERS_TABLE"]


def check_user_in_project(sub, project):
    # check user in project
    response = dynamodb_client.get_item(
        TableName=DYNAMO_PROJECT_USERS_TABLE,
        Key={"name": {"S": project}, "uid": {"S": sub}},
    )

    assert "Item" in response, "User not found in project"
