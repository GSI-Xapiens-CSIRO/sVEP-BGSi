import os
import json
import gzip

import boto3

from shared.utils import get_sns_event, sns_publish, s3, handle_failed_execution
from shared.indexutils import create_index
from shared.dynamodb import update_clinic_job


# AWS clients as s3 is a resource
s3_client = boto3.client("s3")

# Environment variables
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
SVEP_RESULTS = os.environ["SVEP_RESULTS"]
CONCATPAGES_SNS_TOPIC_ARN = os.environ["CONCATPAGES_SNS_TOPIC_ARN"]
CREATEPAGES_SNS_TOPIC_ARN = os.environ["CREATEPAGES_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'


def append(page_keys, page_num, prefix):
    filename = f"{prefix}{page_num}concatenated.tsv"
    content = []
    for page_key in page_keys:
        obj = s3_client.get_object(Bucket=SVEP_REGIONS, Key=page_key)
        body = obj["Body"].read()
        content.append(body)
    s3.Object(SVEP_REGIONS, filename).put(Body=(b"\n".join(content)))


def publish_result(request_id, project, page_keys, page_num, prefix):
    filename = f"{prefix}{page_num}concatenated.tsv"
    print(prefix)
    bucket_len = len(s3_list_objects(SVEP_REGIONS, prefix))
    if bucket_len != page_num:
        print("calling itself again to make sure all files are done.")
        sns_publish(
            CREATEPAGES_SNS_TOPIC_ARN,
            {
                "requestId": request_id,
                "project": project,
                "pageKeys": page_keys,
                "pageNum": page_num,
                "prefix": prefix,
                "dontAppend": 1,
                "lastPage": 1,
            },
        )
    elif bucket_len == page_num and bucket_len > 10:
        new_prefix = f"{prefix}_round"
        prefix_files = s3_list_objects(SVEP_REGIONS, prefix)
        prefix_keys = [d["Key"] for d in prefix_files]
        all_keys = [prefix_keys[x : x + 20] for x in range(0, len(prefix_keys), 20)]
        print(f"length of all keys = {len(all_keys)}")
        total_len = len(all_keys)
        for idx, key in enumerate(all_keys, start=1):
            sns_publish(
                CREATEPAGES_SNS_TOPIC_ARN,
                {
                    "requestId": request_id,
                    "project": project,
                    "pageKeys": all_keys[idx - 1],
                    "pageNum": idx,
                    "prefix": new_prefix,
                    "lastPage": 1 if idx == total_len else 0,
                },
            )
    elif bucket_len == page_num and bucket_len < 10:
        print("last page and all combined")
        files = s3_list_objects(SVEP_REGIONS, prefix)
        all_keys = [d["Key"] for d in files]
        sns_publish(
            CONCATPAGES_SNS_TOPIC_ARN,
            {
                "requestId": request_id,
                "project": project,
                "allKeys": all_keys,
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
        prefix_files = s3_list_objects(SVEP_REGIONS, prefix)
        prefix_keys = prefix_files[0]["Key"]
        copy_source = {"Bucket": SVEP_REGIONS, "Key": prefix_keys}
        s3_client.copy(copy_source, SVEP_RESULTS, result_file)
        # download the file and create index
        s3_client.download_file(SVEP_REGIONS, prefix_keys, f"/tmp/{filename}")

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

        update_clinic_job(request_id, job_status="completed")


def s3_list_objects(bucket, prefix):
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return response["Contents"]


def lambda_handler(event, _):
    message = get_sns_event(event)
    request_id = message["requestId"]
    project = message["project"]
    try:
        page_keys = message["pageKeys"]
        page_num = message["pageNum"]
        prefix = message["prefix"]
        last_page = message["lastPage"]
        dont_append = message.get("dontAppend", 0)
        if dont_append == 0:
            append(page_keys, page_num, prefix)
        if last_page == 1:
            publish_result(request_id, project, page_keys, page_num, prefix)
    except Exception as e:
        handle_failed_execution(request_id, e)
