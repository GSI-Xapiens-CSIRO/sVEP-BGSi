import os
import sys

import boto3
import botocore
from moto import mock_aws

from .env import keys  # to inject keys into the environment


@mock_aws
def setup_resources():
    # Create a Cognito User Pool
    cognito_client = boto3.client(
        "cognito-idp", region_name=os.environ["AWS_DEFAULT_REGION"]
    )
    dynamodb_client = boto3.client(
        "dynamodb", region_name=os.environ["AWS_DEFAULT_REGION"]
    )
    sagemaker_client = boto3.client(
        "sagemaker", region_name=os.environ["AWS_DEFAULT_REGION"]
    )

    # create cognito user pool
    response = cognito_client.create_user_pool(
        PoolName=keys["COGNITO_USER_POOL_ID"],
        Policies={
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": True,
                "RequireLowercase": True,
                "RequireNumbers": True,
                "RequireSymbols": True,
            }
        },
    )

    userpool_id = response["UserPool"]["Id"]
    os.environ["COGNITO_USER_POOL_ID"] = userpool_id

    # create cognito users
    # Admin
    admin_user = cognito_client.admin_create_user(
        UserPoolId=userpool_id,
        Username="admin@example.com",
        TemporaryPassword="admin1234",
        MessageAction="SUPPRESS",
        UserAttributes=[
            {"Name": "email", "Value": "admin@example.com"},
            {"Name": "given_name", "Value": "Admin"},
            {"Name": "family_name", "Value": "Admin"},
            {"Name": "email_verified", "Value": "true"},
        ],
    )
    # Guest
    guest_user = cognito_client.admin_create_user(
        UserPoolId=userpool_id,
        Username="guest@example.com",
        TemporaryPassword="guest1234",
        MessageAction="SUPPRESS",
        UserAttributes=[
            {"Name": "email", "Value": "guest@example.com"},
            {"Name": "given_name", "Value": "Guest"},
            {"Name": "family_name", "Value": "Guest"},
            {"Name": "email_verified", "Value": "true"},
        ],
    )

    admin_sub = next(
        filter(lambda x: x["Name"] == "sub", admin_user["User"]["Attributes"])
    )["Value"]
    guest_sub = next(
        filter(lambda x: x["Name"] == "sub", guest_user["User"]["Attributes"])
    )["Value"]

    return {
        "admin_sub": admin_sub,
        "guest_sub": guest_sub,
        "userpool_id": userpool_id,
    }


if __name__ == "__main__":
    setup_resources()
