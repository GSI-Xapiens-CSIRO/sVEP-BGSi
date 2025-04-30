import json
import time
import os
import boto3

from shared.dynamodb import scan_pending_jobs, bulk_delete_jobs, send_job_email

s3 = boto3.client("s3")

SVEP_TEMP = os.environ["SVEP_TEMP"]

MAX_RETRIES = 5
RETRY_DELAY = 30


def clean_bucket(bucket, job_id):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=job_id)

    print(
        f"[Cron Jobs - clean_bucket()]: Cleaning bucket {bucket} for job_id {job_id}."
    )

    if "Contents" in response:
        delete_objects = [{"Key": d["Key"]} for d in response["Contents"]]
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_objects})


def clean_with_retries(bucket, job_id):
    retries = 0
    while retries < MAX_RETRIES:
        print(f"Attempt {retries + 1} to clean {bucket} for {job_id}")
        clean_bucket(bucket, job_id)
        response = s3.list_objects_v2(Bucket=bucket, Prefix=job_id)
        if "Contents" not in response:
            print(
                f"[Cron Jobs - clean_with_retries()]: Cleanup successful for {job_id}. No more objects found."
            )
            break
        print(
            f"[Cron Jobs - clean_with_retries()]: Retrying cleanup in {RETRY_DELAY} seconds..."
        )
        time.sleep(RETRY_DELAY)
        retries += 1
    if retries == MAX_RETRIES:
        print(
            f"[Cron Jobs - clean_with_retries()]: Max retries reached for cleanup of {job_id}. Some files may remain."
        )


def lambda_handler(event, _):
    if event.get("source") == "aws.events":
        pending_jobs = scan_pending_jobs()

        print(f"[Cron Jobs]: Found {len(pending_jobs)} pending jobs to delete.")
        print(f"[Cron Jobs]: Pending jobs {json.dumps(pending_jobs, default=str)}")

        if len(pending_jobs) > 0:
            print("[Cron Jobs]: Deleting pending jobs.")
            # Delete the pending jobs
            bulk_delete_jobs(pending_jobs)

            for job in pending_jobs:
                job_id = job["job_id"]["S"]
                user_id = job.get("uid", {}).get("S")
                project_name = job.get("project_name", {}).get("S")
                input_vcf = job.get("input_vcf", {}).get("S")
                job_status = job.get("job_status", {}).get("S")

                print(f"[Cron Jobs]: Cleaning bucket for job {job_id}.")
                clean_with_retries(SVEP_TEMP, job_id)

                print(f"[Cron Jobs]: Sending email for job {job_id} to user {user_id}.")

                send_job_email(
                    job_id=job_id,
                    job_status=job_status,
                    project_name=project_name,
                    input_vcf=input_vcf,
                    user_id=user_id,
                    is_from_failed_execution=True,  # Set true to avoid re running query_clinic_job
                )

                time.sleep(1)
        else:
            print("[Cron Jobs]: No pending jobs to delete.")
