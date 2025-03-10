import json
import os
import subprocess

from shared.utils import (
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
PLUGIN_UPDOWNSTREAM_SNS_TOPIC_ARN = os.environ["PLUGIN_UPDOWNSTREAM_SNS_TOPIC_ARN"]
QUERY_GTF_SNS_TOPIC_ARN = os.environ["QUERY_GTF_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'
TOPICS = [
    PLUGIN_CONSEQUENCE_SNS_TOPIC_ARN,
    PLUGIN_UPDOWNSTREAM_SNS_TOPIC_ARN,
]

MILLISECONDS_BEFORE_SPLIT = 4000
PAYLOAD_SIZE = 260000

# Download reference genome and index
download_vcf(BUCKET_NAME, REFERENCE_GENOME)


def overlap_feature(request_id, all_coords, base_id, timer, chrom_mapping):
    results = []
    tot_size = 0
    counter = 0
    for idx, coord in enumerate(all_coords):
        chrom, pos, ref, alt = coord.split("\t")
        loc = f"{chrom_mapping[chrom]}:{pos}-{pos}"
        local_file = f"/tmp/{REFERENCE_GENOME}"
        args = ["tabix", local_file, loc]
        query_process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/tmp",
            encoding="ascii",
        )
        main_data = query_process.stdout.read().rstrip("\n").split("\n")
        data = {
            "chrom": chrom,
            "pos": pos,
            "ref": ref,
            "alt": alt,
            "data": main_data,
        }
        cur_size = len(json.dumps(data, separators=(",", ":"))) + 1
        tot_size += cur_size
        if tot_size < PAYLOAD_SIZE:
            results.append(data)
            if timer.out_of_time():
                # should only be executed in very few cases.
                counter += 1

                send_data_to_plugins(
                    request_id, base_id, counter, results, chrom_mapping
                )
                send_data_to_self(request_id, base_id, all_coords[idx:], chrom_mapping)
                return
        else:
            counter += 1
            send_data_to_plugins(request_id, base_id, counter, results, chrom_mapping)
            if timer.out_of_time():
                send_data_to_self(request_id, base_id, all_coords[idx:], chrom_mapping)
                return
            else:
                results = [data]
                tot_size = cur_size
    counter += 1
    send_data_to_plugins(request_id, base_id, counter, results, chrom_mapping)


def send_data_to_plugins(request_id, base_id, counter, results, chrom_mapping):
    for topic in TOPICS:
        start_function(
            topic_arn=topic,
            base_filename=f"{base_id}_{counter}",
            message={
                "requestId": request_id,
                "snsData": results,
                "mapping": chrom_mapping,
            },
        )


def send_data_to_self(request_id, base_id, remaining_coords, chrom_mapping):
    print("Less Time remaining - call itself.")
    start_function(
        topic_arn=QUERY_GTF_SNS_TOPIC_ARN,
        base_filename=base_id,
        message={
            "requestId": request_id,
            "coords": remaining_coords,
            "mapping": chrom_mapping,
        },
        resend=True,
    )


def lambda_handler(event, context):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    timer = Timer(context, MILLISECONDS_BEFORE_SPLIT)
    request_id = message["requestId"]
    coords = message["coords"]
    chrom_mapping = message["mapping"]
    try:
        base_id = orchestrator.temp_file_name
        overlap_feature(request_id, coords, base_id, timer, chrom_mapping)
        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
