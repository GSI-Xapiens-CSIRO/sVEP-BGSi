import os
import time

import boto3

from lambda_utils import get_sns_event, sns_publish
import s3fs


# AWS clients and resources
fs = s3fs.S3FileSystem(anon=False)
s3 = boto3.client('s3')

# Environment variables
RESULT_SUFFIX = os.environ['RESULT_SUFFIX']
SVEP_REGIONS = os.environ['SVEP_REGIONS']
SVEP_RESULTS = os.environ['SVEP_RESULTS']
CONCATPAGES_SNS_TOPIC_ARN = os.environ['CONCATPAGES_SNS_TOPIC_ARN']
os.environ['PATH'] += f':{os.environ["LAMBDA_TASK_ROOT"]}'


def clean_regions(request_id):
    response = s3.list_objects_v2(Bucket=SVEP_REGIONS, Prefix=request_id)
    if 'Contents' in response:
        paths = [
            f'{SVEP_REGIONS}/{d["Key"]}'
            for d in response['Contents']
        ]
        fs.bulk_delete(pathlist=paths)


def publish_result(request_id, user_id, all_keys, last_file, page_num, prefix):
    start_time = time.time()
    filename = f'{request_id}{RESULT_SUFFIX}'
    file_path = f's3://{SVEP_RESULTS}/private/{user_id}/svep-results/{filename}'
    response = s3.list_objects_v2(Bucket=SVEP_REGIONS, Prefix=prefix)
    if len(response['Contents']) == page_num:
        paths = [
            f'{SVEP_REGIONS}/{d}'
            for d in all_keys
        ]
        fs.merge(path=file_path, filelist=paths)
        print(f"time taken = {(time.time()-start_time) * 1000}")
        print("Done concatenating")
        clean_regions(request_id)
    else:
        print("createPages failed to create one of the page")
        sns_publish(CONCATPAGES_SNS_TOPIC_ARN, {
            'requestId': request_id,
            'lastFile': last_file,
            'pageNum': page_num,
        })


def lambda_handler(event, _):
    message = get_sns_event(event)
    request_id = message['requestId']
    user_id = message['userId']
    all_keys = message['allKeys']
    last_file = message['lastFile']
    page_num = message['pageNum']
    prefix = message['prefix']
    publish_result(request_id, user_id, all_keys, last_file, page_num, prefix)
