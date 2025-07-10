import os

from shared.indexutils import filename_order
from shared.utils import orchestration, s3_list_objects


# Environment variables
CREATEPAGES_SNS_TOPIC_ARN = os.environ["CREATEPAGES_SNS_TOPIC_ARN"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
PAGE_SIZE = 600


def concat(orc, project, request_id):
    keys = sorted(s3_list_objects(SVEP_REGIONS, request_id), key=filename_order)
    message = {
        "prefix": f"{request_id}_page",
        "project": project,
    }
    page_num = 1
    while True:
        page_keys = keys[:PAGE_SIZE]
        keys = keys[PAGE_SIZE:]
        message.update(
            {
                "pageKeys": page_keys,
                "pageNum": page_num,
                "lastPage": 0 if keys else 1,
            }
        )
        orc.start_function(CREATEPAGES_SNS_TOPIC_ARN, message)
        if not keys:
            print(f"last page: {page_num}")
            break
        page_num += 1
    print("Finished sending to createPages")


def lambda_handler(event, _):
    with orchestration(event) as orc:
        project = orc.message["project"]
        request_id = orc.request_id
        concat(orc, project, request_id)
