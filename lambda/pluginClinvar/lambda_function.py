import os
import subprocess


from shared.utils import (
    Orchestrator,
    s3,
    download_bedfile,
    handle_failed_execution,
    start_function,
)

# Environment variables
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
CLINVAR_REFERENCE = os.environ["CLINVAR_REFERENCE"]
FORMAT_OUTPUT_SNS_TOPIC_ARN = os.environ["FORMAT_OUTPUT_SNS_TOPIC_ARN"]
PLUGIN_SIFT_SNS_TOPIC_ARN = os.environ["PLUGIN_SIFT_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'
# Just the columns after the identifying columns
CLINVAR_COLUMNS = [
    "variationId",
    "rsId",
    "omimId",
    "classification",
    "conditions",
    "clinSig",
    "reviewStatus",
    "lastEvaluated",
    "accession",
    "pubmed",
]

# Download reference genome and index
download_bedfile(BUCKET_NAME, CLINVAR_REFERENCE)


def add_clinvar_columns(in_rows, ref_chrom):
    num_rows_hit = 0
    results = []
    for in_row in in_rows:
        _, positions = in_row["region"].split(":")
        row_start, row_end = positions.split("-")
        alt = in_row["alt"]
        loc = f"{ref_chrom}:{positions}"
        local_file = f"/tmp/{CLINVAR_REFERENCE}"
        args = [
            "tabix",
            local_file,
            loc,
        ]
        query_process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/tmp",
            encoding="utf-8",
        )
        main_data = query_process.stdout.read().rstrip("\n").split("\n")
        is_matched = False
        for data in main_data:
            if not data:
                continue
            _, bed_start, bed_end, _, bed_alt, *clinvar_data = data.split("\t")
            if (
                bed_alt == alt
                and bed_end == row_end
                and int(bed_start) + 1 == int(row_start)
            ):
                is_matched = True
                results.append(
                    dict(
                        **in_row,
                        **{
                            col_name: clinvar_datum
                            for col_name, clinvar_datum in zip(
                                CLINVAR_COLUMNS, clinvar_data
                            )
                        },
                    )
                )
        if is_matched:
            num_rows_hit += 1
    print(
        f"Matched {len(results)} rows in clinvar from {num_rows_hit} matching input rows"
    )
    return results


def lambda_handler(event, _):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]
    ref_chrom = message["refChrom"]
    request_id = message["requestId"]

    try:
        sns_data = add_clinvar_columns(sns_data, ref_chrom)
        base_filename = orchestrator.temp_file_name
        # start_function(
        #     topic_arn=PLUGIN_SIFT_SNS_TOPIC_ARN,
        #     base_filename=base_filename,
        #     message={
        #         "snsData": sns_data,
        #         "refChrom": ref_chrom,
        #     },
        # )
        # TODO Delete formatOutput function call (Latest plugin will call this)
        start_function(
            topic_arn=FORMAT_OUTPUT_SNS_TOPIC_ARN,
            base_filename=base_filename,
            message={
                "requestId": request_id,
                "snsData": sns_data,
            },
        )
        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
