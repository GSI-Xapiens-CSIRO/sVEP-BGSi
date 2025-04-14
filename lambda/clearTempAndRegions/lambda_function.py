import time
import json
import os
import boto3

s3 = boto3.client("s3")

SVEP_TEMP = os.environ["SVEP_TEMP"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]

MAX_RETRIES = 5
RETRY_DELAY = 30


def clean_bucket(bucket, request_id):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=request_id)
    if "Contents" in response:
        delete_objects = [{"Key": d["Key"]} for d in response["Contents"]]
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_objects})


def clean_with_retries(bucket, request_id):
    retries = 0
    while retries < MAX_RETRIES:
        print(f"Attempt {retries + 1} to clean {bucket} for {request_id}")
        clean_bucket(bucket, request_id)
        response = s3.list_objects_v2(Bucket=bucket, Prefix=request_id)
        if "Contents" not in response:
            print(f"Cleanup successful for {request_id}. No more objects found.")
            break
        print(f"Retrying cleanup in {RETRY_DELAY} seconds...")
        time.sleep(RETRY_DELAY)
        retries += 1
    if retries == MAX_RETRIES:
        print(
            f"Max retries reached for cleanup of {request_id}. Some files may remain."
        )


def lambda_handler(event, _):
    print(f"Event received: {json.dumps(event)}")
    for record in event["Records"]:
        job_id = record["dynamodb"]["Keys"]["job_id"]["S"]
        old_job_status = record["dynamodb"]["OldImage"].get("job_status", {}).get("S")
        new_job_status = record["dynamodb"]["NewImage"].get("job_status", {}).get("S")
        if old_job_status != "failed" and new_job_status == "failed":
            print(f"Job {job_id} failed. Cleaning regions in buckets.")
            clean_with_retries(SVEP_TEMP, job_id)
            clean_with_retries(SVEP_REGIONS, job_id)
        else:
            print(f"Job {job_id} status is not failed, skipping cleanup.")
