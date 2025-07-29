from datetime import datetime, timedelta
import json
import os

from shared.utils import LoggingClient, handle_failed_execution


SVEP_BATCH_SUBMIT_QUEUE_URL = os.environ["SVEP_BATCH_SUBMIT_QUEUE_URL"]
INIT_QUERY_SNS_TOPIC_ARN = os.environ["INIT_QUERY_SNS_TOPIC_ARN"]
LAMBDA_CONCURRENCY_MARGIN = os.environ["LAMBDA_CONCURRENCY_MARGIN"]

cloudwatch_client = LoggingClient("cloudwatch")
lambda_client = LoggingClient("lambda")
sns_client = LoggingClient("sns")
sqs_client = LoggingClient("sqs")


def get_concurrent_executions():
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=2)

    response = cloudwatch_client.get_metric_statistics(
        Namespace="AWS/Lambda",
        MetricName="ConcurrentExecutions",
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=["Maximum"],
    )

    if response["Datapoints"]:
        datapoints = sorted(response["Datapoints"], key=lambda x: x["Timestamp"])
        current_total = int(datapoints[-1]["Maximum"])
        print(f"Account-level concurrent executions (all functions): {current_total}")
        return current_total
    else:
        print("No data points found for concurrent executions.")
        return 0


def should_process_more_jobs(concurrent_execs):
    settings = lambda_client.get_account_settings()
    concurrent_exec_limit = settings["AccountLimit"]["ConcurrentExecutions"]
    margin = int(LAMBDA_CONCURRENCY_MARGIN)
    usable_capacity = concurrent_exec_limit - margin
    capacity_remaining_after_margin = usable_capacity - concurrent_execs

    return (
        capacity_remaining_after_margin > 0,
        capacity_remaining_after_margin,
        concurrent_execs,
    )


def lambda_handler(event, context):
    if event["source"] == "aws.events":
        print(f"Event received: {json.dumps(event)}")

        response = sqs_client.receive_message(
            QueueUrl=SVEP_BATCH_SUBMIT_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=0,
        )

        if "Messages" not in response:
            return

        concurrent_execs = get_concurrent_executions()

        (
            should_process,
            capacity_remaining_after_margin,
            current_usage,
        ) = should_process_more_jobs(concurrent_execs)

        if not should_process:
            print(
                f"Insufficient capacity to process new more jobs. "
                f"Current usage: {current_usage}, "
                f"Safety margin: {LAMBDA_CONCURRENCY_MARGIN}, "
                f"Would need {abs(capacity_remaining_after_margin)} less concurrent executions. "
            )
            return

        print(
            f"Starting new job. "
            f"Current usage: {current_usage}, "
            f"Safety margin: {LAMBDA_CONCURRENCY_MARGIN}, "
            f"Remaining capacity after margin: {capacity_remaining_after_margin}, "
        )

        for message in response["Messages"]:
            message_body = json.loads(message.get("Body", "{}"))
            if request_id := message_body.get("requestId"):
                try:
                    sns_client.publish(
                        TopicArn=INIT_QUERY_SNS_TOPIC_ARN,
                        Message=json.dumps(message_body),
                    )

                except Exception as e:
                    handle_failed_execution(
                        request_id,
                        error_message=f"Failed to publish message to SNS topic: {str(e)}",
                    )

            else:
                print(
                    f"Message does not contain 'requestId': {json.dumps(message_body)}"
                )

        sqs_client.delete_message(
            QueueUrl=SVEP_BATCH_SUBMIT_QUEUE_URL,
            ReceiptHandle=response["Messages"][0]["ReceiptHandle"],
        )
