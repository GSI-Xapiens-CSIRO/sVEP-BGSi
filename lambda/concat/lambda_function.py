import os

import boto3

from shared.utils import get_sns_event, sns_publish


# AWS clients and resources
s3 = boto3.client("s3")

# Environment variables
CREATEPAGES_SNS_TOPIC_ARN = os.environ["CREATEPAGES_SNS_TOPIC_ARN"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]


def concat(request_id, project):
    page_num = 0
    paginator = s3.get_paginator("list_objects_v2")
    # Change later on
    operation_parameters = {
        "Bucket": SVEP_REGIONS,
        "Prefix": request_id,
        "PaginationConfig": {"PageSize": 600},
    }
    page_iterator = paginator.paginate(**operation_parameters)
    message = {
        "requestId": request_id,
        "prefix": f"{request_id}_page",
        "project": project,
    }
    for page in page_iterator:
        print(page)
        page_contents = page["Contents"]
        page_keys = [d["Key"] for d in page_contents]
        page_num += 1
        message.update(
            {
                "pageKeys": page_keys,
                "pageNum": page_num,
            }
        )
        if "NextContinuationToken" in page:
            message["lastPage"] = 0
        else:
            print("last page")
            print(page_num)
            message["lastPage"] = 1
        sns_publish(CREATEPAGES_SNS_TOPIC_ARN, message)
    print("Finished sending to createPages")


def lambda_handler(event, _):
    message = get_sns_event(event)
    request_id = message["requestId"]
    project = message["project"]
    concat(request_id, project)
