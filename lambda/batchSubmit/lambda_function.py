import json
import os
import traceback

from botocore.client import ClientError
from uuid import uuid4 as uuid

from shared.apiutils import bad_request, bundle_response
from shared.dynamodb import check_user_in_project, update_clinic_job
from shared.utils import LoggingClient
from dynamodb import batch_check_duplicate_job_name


DPORTAL_BUCKET = os.environ["DPORTAL_BUCKET"]
SVEP_BATCH_SUBMIT_QUEUE_URL = os.environ["SVEP_BATCH_SUBMIT_QUEUE_URL"]
DYNAMO_CLINIC_JOBS_TABLE = os.environ["DYNAMO_CLINIC_JOBS_TABLE"]

sqs_client = LoggingClient("sqs")
dynamodb_client = LoggingClient("dynamodb")


def create_job_entries(jobs, project, sub):
    job_entries = []
    for job in jobs:
        source_vcf_key = (
            f"s3://{DPORTAL_BUCKET}/projects/{project}/project-files/{job["filename"]}"
        )
        request_id = str(uuid())
        job_entry = {
            "Id": request_id,
            "MessageBody": json.dumps(
                {
                    "sub": sub,
                    "requestId": request_id,
                    "projectName": project,
                    "location": source_vcf_key,
                    "filename": job["filename"],
                    "jobName": job["jobName"],
                    "batchJob": True,
                }
            ),
            "DelaySeconds": 0,
        }
        job_entries.append(job_entry)
    return job_entries


def batch_submit(job_entries, sub):
    successful_jobs = []
    failed_jobs = []

    for i in range(0, len(job_entries), 10):
        message_batch = job_entries[i : i + 10]

        try:
            response = sqs_client.send_message_batch(
                QueueUrl=SVEP_BATCH_SUBMIT_QUEUE_URL, Entries=message_batch
            )

            for successful in response.get("Successful", []):
                original_entry = next(
                    job_entry
                    for job_entry in message_batch
                    if job_entry["Id"] == successful["Id"]
                )
                successful_jobs.append(original_entry)

            for failed in response.get("Failed", []):
                original_entry = next(
                    job_entry
                    for job_entry in message_batch
                    if job_entry["Id"] == failed["Id"]
                )
                failed_jobs.append(original_entry)

        except Exception as e:
            traceback.print_exc()
            failed_jobs.extend(message_batch)

        finally:
            if successful_jobs:
                job_data = list(
                    map(lambda job: json.loads(job["MessageBody"]), successful_jobs)
                )
                for job in job_data:
                    update_clinic_job(
                        job_id=job["requestId"],
                        job_name=job["jobName"],
                        job_status="queued",
                        project_name=job["projectName"],
                        input_vcf=job["filename"],
                        user_id=sub,
                        skip_email=True,
                    )

    return successful_jobs, failed_jobs


def lambda_handler(event, _):
    print(f"Event received: {json.dumps(event)}")
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]

    event_body = event.get("body")
    if not event_body:
        return bad_request("No body sent with request.")
    try:
        body_dict = json.loads(event_body)
        project = body_dict["projectName"]
        jobs = body_dict["jobs"]

        check_user_in_project(sub, project)
    except ValueError:
        return bad_request("Error parsing request body, Expected JSON.")

    try:
        job_names = list(map(lambda x: x["jobName"], jobs))
        duplicates = batch_check_duplicate_job_name(job_names, project)

        if duplicates:
            return bad_request(
                f"The following job names already exist: {", ".join(duplicates)}"
            )

    except ClientError as e:
        return bad_request(
            "Unable to check existing jobs for naming conflicts. Please contact an AWS administrator."
        )

    job_entries = create_job_entries(jobs, project, sub)

    successful_jobs, failed_jobs = batch_submit(job_entries, sub)

    return bundle_response(
        200,
        {
            "Response": f"{len(successful_jobs)}/{len(successful_jobs) + len(failed_jobs)} queued for processing.",
            "ProjectName": project,
            "Success": True,
        },
    )
