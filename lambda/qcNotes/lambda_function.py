import subprocess
import os
import boto3
import json
from shared.apiutils import bad_request, bundle_response


s3_client = boto3.client("s3")
BUCKET_NAME = os.environ["FILE_LOCATION"]


def get_s3_file_content_if_exists(bucket_name, file_name):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        return response["Body"].read().decode("utf-8")
    except s3_client.exceptions.NoSuchKey:
        return None
    except Exception as e:
        print(f"Error retrieving file {file_name} from bucket {bucket_name}: {str(e)}")
        return None


def get_notes(project_name, file_name):
    notes_file_name = f"projects/{project_name}/qc-figures/{file_name}/notes.txt"
    notes_content = get_s3_file_content_if_exists(BUCKET_NAME, notes_file_name)

    return bundle_response(
        200,
        {
            "success": True,
            "notes": notes_content,
        },
    )


def update_notes(project_name, file_name, notes):
    notes_file_name = f"projects/{project_name}/qc-figures/{file_name}/notes.txt"
    s3_client.put_object(Bucket=BUCKET_NAME, Key=notes_file_name, Body=notes)

    return bundle_response(
        200,
        {
            "success": True,
            "message": "Notes updated successfully.",
        },
    )

def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    method = event["httpMethod"].upper()

    try:
        match method:
            case "GET":
                project_name = event["queryStringParameters"]["projectName"]
                file_name = event["queryStringParameters"]["fileName"]
                return get_notes(project_name, file_name)

            case "POST":
                project_name = event["queryStringParameters"]["projectName"]
                file_name = event["queryStringParameters"]["fileName"]
                notes = json.loads(event["body"] or "\"\"")
                return update_notes(project_name, file_name, notes)

    except Exception as e:
        print(f"Error parsing request body: {str(e)}")
        return bundle_response(
            500,
            {
                "success": False,
                "error": f"Error fetching notes: {str(e)}",
            },
        )
