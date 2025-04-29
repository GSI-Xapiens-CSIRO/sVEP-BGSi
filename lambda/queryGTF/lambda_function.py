import json
import os

from shared.utils import (
    CheckedProcess,
    download_vcf,
    Orchestrator,
    start_function,
    Timer,
    handle_failed_execution,
)


# Environment variables
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
REFERENCE_GENOME = os.environ["REFERENCE_GENOME"]
PLUGIN_CONSEQUENCE_SNS_TOPIC_ARN = os.environ["PLUGIN_CONSEQUENCE_SNS_TOPIC_ARN"]
QUERY_GTF_SNS_TOPIC_ARN = os.environ["QUERY_GTF_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'
TOPICS = [
    PLUGIN_CONSEQUENCE_SNS_TOPIC_ARN,
]

MILLISECONDS_BEFORE_SPLIT = 4000
PAYLOAD_SIZE = 260000

# Download reference genome and index
download_vcf(BUCKET_NAME, REFERENCE_GENOME)


def overlap_feature(request_id, all_coords, base_id, timer, ref_chrom):
    results = []
    tot_size = 0
    counter = 0
    for idx, data in enumerate(all_coords):
        pos = data["posVcf"]
        loc = f"{ref_chrom}:{pos}-{pos}"
        local_file = f"/tmp/{REFERENCE_GENOME}"
        args = ["tabix", local_file, loc]
        query_process = CheckedProcess(args)
        main_data = query_process.stdout.read().rstrip("\n").split("\n")
        query_process.check()
        data["data"] = main_data
        cur_size = len(json.dumps(data, separators=(",", ":"))) + 1
        tot_size += cur_size
        if tot_size < PAYLOAD_SIZE:
            results.append(data)
            if timer.out_of_time():
                # should only be executed in very few cases.
                counter += 1

                send_data_to_plugins(request_id, base_id, counter, results, ref_chrom)
                send_data_to_self(request_id, base_id, all_coords[idx:], ref_chrom)
                return
        else:
            counter += 1
            send_data_to_plugins(request_id, base_id, counter, results, ref_chrom)
            results = [data]
            tot_size = cur_size
            if timer.out_of_time():
                send_data_to_self(request_id, base_id, all_coords[idx:], ref_chrom)
                break
    counter += 1
    send_data_to_plugins(request_id, base_id, counter, results, ref_chrom)


def send_data_to_plugins(request_id, base_id, counter, results, ref_chrom):
    for topic in TOPICS:
        start_function(
            topic_arn=topic,
            base_filename=f"{base_id}_{counter}",
            message={
                "requestId": request_id,
                "snsData": results,
                "refChrom": ref_chrom,
            },
        )


def send_data_to_self(request_id, base_id, remaining_coords, ref_chrom):
    if not remaining_coords:
        return
    print("Less Time remaining - call itself.")
    start_function(
        topic_arn=QUERY_GTF_SNS_TOPIC_ARN,
        base_filename=base_id,
        message={
            "requestId": request_id,
            "coords": remaining_coords,
            "refChrom": ref_chrom,
        },
        resend=True,
    )


def lambda_handler(event, context):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    timer = Timer(context, MILLISECONDS_BEFORE_SPLIT)
    request_id = message["requestId"]
    coords = message["coords"]
    ref_chrom = message["refChrom"]
    try:
        base_id = orchestrator.temp_file_name
        overlap_feature(request_id, coords, base_id, timer, ref_chrom)
        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
