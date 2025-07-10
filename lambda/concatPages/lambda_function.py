import os
import time
import io
import json
import gzip

import boto3

from shared.utils import orchestration
from shared.indexutils import create_index
from shared.dynamodb import update_clinic_job

# AWS S3 client
s3 = boto3.client("s3")

# Environment variables
RESULT_SUFFIX = os.environ["RESULT_SUFFIX"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
SVEP_RESULTS = os.environ["SVEP_RESULTS"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'


def publish_result(orc, request_id, project, all_keys, page_num, prefix):
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
        update_clinic_job(request_id, job_status="completed")
    else:
        print("createPages failed to create one of the page")
        orc.resend_self()


def lambda_handler(event, _):
    with orchestration(event) as orc:
        message = orc.message
        request_id = orc.request_id
        project = message["project"]
        all_keys = message["allKeys"]
        page_num = message["pageNum"]
        prefix = message["prefix"]
        publish_result(orc, request_id, project, all_keys, page_num, prefix)
