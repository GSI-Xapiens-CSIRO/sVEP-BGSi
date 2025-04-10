import json
import os
import subprocess

from shared.utils import (
    Orchestrator,
    s3,
    handle_failed_execution,
    decompress_sns_data,
    compress_sns_data,
    start_function,
)

SVEP_REGIONS = os.environ["SVEP_REGIONS"]
PLUGIN_GNOMAD_EXECUTOR_SNS_TOPIC_ARN = os.environ[
    "PLUGIN_GNOMAD_EXECUTOR_SNS_TOPIC_ARN"
]


def lambda_handler(event, _):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]
    chrom_mapping = message["mapping"]
    request_id = message["requestId"]
    is_completed = message["isCompleted"]

    print(f"[Gnomad] Request ID: {request_id}")

    sns_data = decompress_sns_data(sns_data)

    try:
        rows = [row.split("\t") for row in sns_data.split("\n") if row]
        base_filename = orchestrator.temp_file_name

        if is_completed:
            print(f"[GNOMAD - INFO] Completed")

            filename = f"/tmp/{base_filename}.tsv"
            with open(filename, "w") as tsv_file:
                tsv_file.write(sns_data)
            s3.Bucket(SVEP_REGIONS).upload_file(filename, f"{base_filename}.tsv")
        else:
            print(f"[GNOMAD - INFO] publish to PLUGIN_GNOMAD_EXECUTOR_SNS_TOPIC_ARN")

            last_index = len(rows) - 1
            compressed_sns_data = compress_sns_data(sns_data)

            start_function(
                topic_arn=PLUGIN_GNOMAD_EXECUTOR_SNS_TOPIC_ARN,
                base_filename=base_filename,
                message={
                    "snsData": compressed_sns_data,
                    "mapping": chrom_mapping,
                    "requestId": request_id,
                    "snsIndex": 0,
                    "lastIndex": 1,
                    # "lastIndex": last_index,
                },
            )

        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
