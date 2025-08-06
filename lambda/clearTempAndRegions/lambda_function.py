import time
import json
import os
import boto3

s3 = boto3.client("s3")
sns = boto3.client("sns")

SVEP_TEMP = os.environ["SVEP_TEMP"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
CLEAR_TEMP_AND_REGIONS_SNS_TOPIC_ARN = os.environ[
    "CLEAR_TEMP_AND_REGIONS_SNS_TOPIC_ARN"
]
RETRY_DELAY = 30
MIN_TIME_TO_EXIT = 10  # Minimum time in seconds to exit before Lambda timeout

CLEAN_JOB_STATUS = [
    "failed",
    "completed",
    "expired",
]


class LowTime(Exception):
    pass


def resend_event(event):
    kwargs = {
        "TopicArn": CLEAR_TEMP_AND_REGIONS_SNS_TOPIC_ARN,
        "Message": json.dumps(event),
    }
    print("Calling sns.publish with kwargs:", event)
    response = sns.publish(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def clean_bucket(bucket, request_id):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=request_id)
    if "Contents" in response:
        delete_objects = [{"Key": d["Key"]} for d in response["Contents"]]
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_objects})


def clean_with_retries(bucket, request_id, context):
    retries = 0
    while True:
        print(f"Attempt {retries + 1} to clean {bucket} for {request_id}")
        clean_bucket(bucket, request_id)
        response = s3.list_objects_v2(Bucket=bucket, Prefix=request_id)
        if "Contents" not in response:
            print(f"Cleanup successful for {request_id}. No more objects found.")
            break
        if (
            context.get_remaining_time_in_millis()
            < (RETRY_DELAY + MIN_TIME_TO_EXIT) * 1000
        ):
            print("Stopping retries due to insufficient time.")
            raise LowTime()
        print(f"Retrying cleanup in {RETRY_DELAY} seconds...")
        time.sleep(RETRY_DELAY)
        retries += 1


def lambda_handler(event, context):
    print(f"Event received: {json.dumps(event)}")
    if (records := event["Records"]) and (
        sns_message := records[0].get("Sns", {}).get("Message")
    ) is not None:
        print("Received repeat request from SNS, setting that as the message.")
        event = json.loads(sns_message)
    for record in event["Records"]:
        job_id = record["dynamodb"]["Keys"]["job_id"]["S"]
        old_job_status = record["dynamodb"]["OldImage"].get("svep_status", {}).get("S")
        new_job_status = record["dynamodb"]["NewImage"].get("svep_status", {}).get("S")
        if new_job_status != old_job_status and new_job_status in CLEAN_JOB_STATUS:
            print(f"Job {job_id} {new_job_status}. Cleaning regions in buckets.")
            try:
                clean_with_retries(SVEP_TEMP, job_id, context)
                clean_with_retries(SVEP_REGIONS, job_id, context)
            except LowTime:
                print("Low time remaining, resending event.")
                resend_event(event)
                break
        else:
            print(
                f"Job {job_id} status has not changed or is not in {CLEAN_JOB_STATUS}, skipping cleanup."
            )
