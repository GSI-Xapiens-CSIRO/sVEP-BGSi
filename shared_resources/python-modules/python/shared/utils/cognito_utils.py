import json
import os

import boto3
from botocore.exceptions import ClientError

USER_POOL_ID = os.environ.get("USER_POOL_ID", "")


def get_cognito_user_by_id(uid):
    try:
        cognito_client = boto3.client("cognito-idp")

        response = cognito_client.list_users(
            UserPoolId=USER_POOL_ID, Filter=f'sub = "{uid}"', Limit=1
        )

        # Check if any user was found
        if not response.get("Users"):
            print("[get_cognito_user] - User not found.")
            return None

        # Extract attributes correctly
        user = response["Users"][0]
        attributes = {
            attr["Name"]: attr["Value"] for attr in user.get("Attributes", [])
        }

        print(f"[get_cognito_user] - User found: {json.dumps(attributes)}")

        return {
            "email": attributes.get("email", ""),
            "first_name": attributes.get("given_name", ""),
            "last_name": attributes.get("family_name", ""),
        }

    except ClientError as e:
        print(f"An error occurred: {e.response['Error']['Message']}")
        return None  # Return None if an error occurs
