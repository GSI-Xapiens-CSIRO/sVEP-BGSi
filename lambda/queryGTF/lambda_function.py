import json
import os

from shared.utils import (
    CheckedProcess,
    download_vcf,
    orchestration,
    Timer,
)


# Environment variables
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
FILTER_GENES = set(os.environ["FILTER_GENES"].split(",")) - {""}
REFERENCE_GENOME = os.environ["REFERENCE_GENOME"]
PLUGIN_CONSEQUENCE_SNS_TOPIC_ARN = os.environ["PLUGIN_CONSEQUENCE_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'
TOPICS = [
    PLUGIN_CONSEQUENCE_SNS_TOPIC_ARN,
]

MILLISECONDS_BEFORE_SPLIT = 4000
PAYLOAD_SIZE = 260000

# Download reference genome and index
download_vcf(BUCKET_NAME, REFERENCE_GENOME)


def overlap_feature(orc, all_coords, timer):
    results = []
    tot_size = 0
    records_processed = 0
    records_passed = 0
    for idx, data in enumerate(all_coords):
        pos = data["posVcf"]
        loc = f"{orc.ref_chrom}:{pos}-{pos}"
        local_file = f"/tmp/{REFERENCE_GENOME}"
        args = ["tabix", local_file, loc]
        query_process = CheckedProcess(args)
        main_data = query_process.stdout.read().rstrip("\n").split("\n")
        query_process.check()
        records_processed += len(main_data)
        # Filter out lines that do not contain the gene name
        if FILTER_GENES:
            main_data = [
                line
                for line in main_data
                if (
                    ((start := line.find('gene_name "') + 11) > 10)
                    and (line[start : line.find('"', start)] in FILTER_GENES)
                )
            ]
        if main_data:
            data["data"] = main_data
            records_passed += len(main_data)
            cur_size = len(json.dumps(data, separators=(",", ":"))) + 1
            tot_size += cur_size
            if tot_size < PAYLOAD_SIZE:
                results.append(data)
            else:
                send_data_to_plugins(orc, results)
                results = [data]
                tot_size = cur_size
        if timer.out_of_time():
            send_data_to_self(orc, all_coords[idx:])
            break
    send_data_to_plugins(orc, results)
    print(f"Passed {records_passed}/{records_processed} records with matching genes.")


def send_data_to_plugins(orc, results):
    if not results:
        return
    for topic in TOPICS:
        orc.start_function(
            topic_arn=topic,
            message={
                "snsData": results,
            },
        )


def send_data_to_self(orc, remaining_coords):
    if not remaining_coords:
        return
    print("Less Time remaining - call itself.")
    orc.resend_self(
        message_update={
            "coords": remaining_coords,
        },
    )


def lambda_handler(event, context):
    timer = Timer(context, MILLISECONDS_BEFORE_SPLIT)
    with orchestration(event) as orc:
        coords = orc.message["coords"]
        overlap_feature(orc, coords, timer)
