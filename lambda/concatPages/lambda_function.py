import os
import time
import io
import json
import gzip

import boto3

from shared.utils import (
    get_sns_event,
    sns_publish,
    handle_failed_execution,
)
from shared.indexutils import create_index
from shared.dynamodb import update_clinic_job

# AWS S3 client
s3 = boto3.client("s3")

# Environment variables
RESULT_SUFFIX = os.environ["RESULT_SUFFIX"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
SVEP_RESULTS = os.environ["SVEP_RESULTS"]
CONCATPAGES_SNS_TOPIC_ARN = os.environ["CONCATPAGES_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'


def clean_regions(request_id):
    response = s3.list_objects_v2(Bucket=SVEP_REGIONS, Prefix=request_id)
    if "Contents" in response:
        delete_objects = [{"Key": d["Key"]} for d in response["Contents"]]
        s3.delete_objects(Bucket=SVEP_REGIONS, Delete={"Objects": delete_objects})


def publish_result(request_id, project, all_keys, last_file, page_num, prefix):
    start_time = time.time()
    filename = f"{request_id}{RESULT_SUFFIX}"
    response = s3.list_objects_v2(Bucket=SVEP_REGIONS, Prefix=prefix)
    if len(response["Contents"]) == page_num:
        paths = [f"{SVEP_REGIONS}/{d}" for d in all_keys]
        merged_content = b""
        for file in paths:
            obj = s3.get_object(Bucket=SVEP_REGIONS, Key=file.split("/")[-1])
            merged_content += obj["Body"].read()
        content_stream = io.BytesIO(merged_content)
        index = create_index(content_stream)
        index = json.dumps(index).encode()
        index = gzip.compress(index)
        s3.put_object(
            Bucket=SVEP_RESULTS,
            Key=f"projects/{project}/clinical-workflows/{filename}",
            Body=merged_content,
        )
        s3.put_object(
            Bucket=SVEP_RESULTS,
            Key=f"projects/{project}/clinical-workflows/{filename}.index.json.gz",
            Body=index,
        )
        print(f"time taken = {(time.time()-start_time) * 1000}")
        print("Done concatenating")
        clean_regions(request_id)
        update_clinic_job(request_id, job_status="completed")
    else:
        print("createPages failed to create one of the page")
        sns_publish(
            CONCATPAGES_SNS_TOPIC_ARN,
            {
                "requestId": request_id,
                "lastFile": last_file,
                "pageNum": page_num,
            },
        )


def lambda_handler(event, _):
    message = get_sns_event(event)
    request_id = message["requestId"]
    project = message["project"]
    try:
        all_keys = message["allKeys"]
        last_file = message["lastFile"]
        page_num = message["pageNum"]
        prefix = message["prefix"]
        publish_result(request_id, project, all_keys, last_file, page_num, prefix)
    except Exception as e:
        handle_failed_execution(request_id, e)
