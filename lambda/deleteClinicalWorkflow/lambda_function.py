import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, _):
    if event.get("source") == "aws.events":
        logger.info("Lambda function triggered by cron job.")
