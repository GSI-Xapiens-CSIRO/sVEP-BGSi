import os
import json
import gzip

import boto3

from shared.utils import orchestration, s3, s3_list_objects
from shared.indexutils import create_index, filename_order
from shared.dynamodb import update_clinic_job


# AWS clients as s3 is a resource
s3_client = boto3.client("s3")

# Environment variables
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
SVEP_RESULTS = os.environ["SVEP_RESULTS"]
CONCATPAGES_SNS_TOPIC_ARN = os.environ["CONCATPAGES_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'


def append(page_keys, page_num, prefix):
    filename = f"{prefix}{page_num}concatenated.tsv"
    content = []
    for page_key in page_keys:
        obj = s3_client.get_object(Bucket=SVEP_REGIONS, Key=page_key)
        body = obj["Body"].read()
        content.append(body)
    s3.Object(SVEP_REGIONS, filename).put(Body=(b"\n".join(content)))


def publish_result(orc, request_id, project, page_num, prefix):
    filename = f"{prefix}{page_num}concatenated.tsv"
    print(prefix)
    prefix_keys = sorted(s3_list_objects(SVEP_REGIONS, prefix), key=filename_order)
    bucket_len = len(prefix_keys)
    if bucket_len != page_num:
        print("calling itself again to make sure all files are done.")
        orc.resend_self(
            message_update={
                "dontAppend": 1,
            },
        )
    elif bucket_len == page_num and bucket_len > 10:
        new_prefix = f"{prefix}_round"
        key_groups = [prefix_keys[x : x + 20] for x in range(0, len(prefix_keys), 20)]
        print(f"number of key groups = {len(key_groups)}")
        last_index = len(key_groups) - 1
        for idx, key_group in enumerate(key_groups):
            orc.start_function(
                orc.topic_arn,
                {
                    "project": project,
                    "pageKeys": key_group,
                    "pageNum": idx + 1,
                    "prefix": new_prefix,
                    "lastPage": 1 if idx == last_index else 0,
                },
            )
    elif bucket_len == page_num and bucket_len < 10:
        print("last page and all combined")
        orc.start_function(
            CONCATPAGES_SNS_TOPIC_ARN,
            {
                "project": project,
                "allKeys": prefix_keys,
                "lastFile": filename,
                "pageNum": page_num,
                "prefix": prefix,
            },
        )
        # trigger another lambda to concat all pages
    elif bucket_len == 1:
        result_file = (
            f"s3://{SVEP_RESULTS}/projects/{project}/clinical-workflows/{filename}"
        )
        only_key = prefix_keys[0]
        copy_source = {"Bucket": SVEP_REGIONS, "Key": only_key}
        s3_client.copy(copy_source, SVEP_RESULTS, result_file)
        # download the file and create index
        s3_client.download_file(SVEP_REGIONS, only_key, f"/tmp/{filename}")

        with open(f"/tmp/{filename}", "rb") as fp:
            index = create_index(fp)
            index = json.dumps(index).encode()
            index = gzip.compress(index)
            s3_client.put_object(
                Bucket=SVEP_RESULTS,
                Key=f"{result_file}.index.json.gz",
                Body=index,
            )
        os.remove(f"/tmp/{filename}")

        update_clinic_job(request_id, job_status="completed", skip_email=True)


def lambda_handler(event, _):
    with orchestration(event) as orc:
        message = orc.message
        request_id = orc.request_id
        project = message["project"]
        page_keys = message["pageKeys"]
        page_num = message["pageNum"]
        prefix = message["prefix"]
        last_page = message["lastPage"]
        dont_append = message.get("dontAppend", 0)
        if dont_append == 0:
            append(page_keys, page_num, prefix)
        if last_page == 1:
            publish_result(orc, request_id, project, page_num, prefix)
