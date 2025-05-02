import os
import time

import boto3

from shared.utils import get_sns_event, sns_publish, handle_failed_execution
from shared.dynamodb import query_clinic_job

# AWS clients and resources
s3 = boto3.client("s3")

# Environment variables
CONCAT_SNS_TOPIC_ARN = os.environ["CONCAT_SNS_TOPIC_ARN"]
CONCAT_STARTER_SNS_TOPIC_ARN = os.environ["CONCAT_STARTER_SNS_TOPIC_ARN"]
LIST_INTERVAL = 5
MAX_WAIT_TIME = 2 * 60 * 60  # 2 hours
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
SVEP_TEMP = os.environ["SVEP_TEMP"]


def ready_for_concat(request_id):
    objs = s3.list_objects(Bucket=SVEP_TEMP, Prefix=request_id)
    return "Contents" not in objs


def wait(request_id, project, time_started):
    time_waited = time.time() - time_started
    if time_waited >= MAX_WAIT_TIME:
        print(f"Waited {time_waited} seconds. Giving up.")
        raise Exception(f"Pipeline timed out after {MAX_WAIT_TIME} seconds.")
    time.sleep(LIST_INTERVAL)
    message = {
        "requestId": request_id,
        "project": project,
        "timeStarted": time_started,
    }
    sns_publish(CONCAT_STARTER_SNS_TOPIC_ARN, message)
    # We end here so this environment is available to immediately
    # pick up the published message.


def lambda_handler(event, _):
    message = get_sns_event(event)
    request_id = message["requestId"]
    project = message["project"]
    try:
        time_started = message.get("timeStarted", time.time())
        if ready_for_concat(request_id):
            job = query_clinic_job(request_id)
            # do not start concatenation if the job has already failed
            if job.get("job_status").get("S") == "failed":
                print(f"Job failed. Aborting")
                return
            sns_publish(
                CONCAT_SNS_TOPIC_ARN,
                {
                    "requestId": request_id,
                    "project": project,
                },
            )
        else:
            wait(request_id, project, time_started)
    except Exception as e:
        handle_failed_execution(request_id, e)
