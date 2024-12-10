import os
import time

import boto3

from shared.utils import get_sns_event, sns_publish


# AWS clients and resources
s3 = boto3.client('s3')

# Environment variables
CONCAT_SNS_TOPIC_ARN = os.environ['CONCAT_SNS_TOPIC_ARN']
CONCAT_STARTER_SNS_TOPIC_ARN = os.environ['CONCAT_STARTER_SNS_TOPIC_ARN']
LIST_INTERVAL = 5
MAX_WAIT_TIME = 2 * 60 * 60  # 2 hours
SVEP_REGIONS = os.environ['SVEP_REGIONS']
SVEP_TEMP = os.environ['SVEP_TEMP']


def ready_for_concat(request_id):
    objs = s3.list_objects(Bucket=SVEP_TEMP, Prefix=request_id)
    return 'Contents' not in objs


def wait(request_id, user_id, time_started):
    time_waited = time.time() - time_started
    if time_waited >= MAX_WAIT_TIME:
        print(f"Waited {time_waited} seconds. Giving up.")
        return
    time.sleep(LIST_INTERVAL)
    message = {
        'requestId': request_id,
        'userId': user_id,
        'timeStarted': time_started,
    }
    sns_publish(CONCAT_STARTER_SNS_TOPIC_ARN, message)
    # We end here so this environment is available to immediately
    # pick up the published message.


def lambda_handler(event, _):
    message = get_sns_event(event)
    request_id = message['requestId']
    user_id = message['userId']
    time_started = message.get('timeStarted', time.time())
    if ready_for_concat(request_id):
        sns_publish(CONCAT_SNS_TOPIC_ARN, {
            'requestId': request_id,
            'userId': user_id,
        })
    else:
        wait(request_id, user_id, time_started)
