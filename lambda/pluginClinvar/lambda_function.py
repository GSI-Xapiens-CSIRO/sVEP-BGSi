import os
import subprocess


import urllib.parse
from shared.utils import (
    Orchestrator,
    s3,
    download_bedfile,
    handle_failed_execution,
    start_function,
)

# Environment variables
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
CLINVAR_REFERENCE = os.environ["CLINVAR_REFERENCE"]
PLUGIN_SIFT_SNS_TOPIC_ARN = os.environ["PLUGIN_SIFT_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

# Download reference genome and index
download_bedfile(BUCKET_NAME, CLINVAR_REFERENCE)


def add_clinvar_columns(in_rows, chrom_mapping):
    results = []
    for in_row in in_rows:
        chrom, positions = in_row[2].split(":")
        row_start, row_end = positions.split("-")
        alt = in_row[3]
        loc = f"{chrom_mapping[chrom]}:{positions}"
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
            encoding="ascii",
        )
        main_data = query_process.stdout.read().rstrip("\n").split("\n")
        # is_matched = False
        for data in main_data:
            metadata = data.split("\t")
            if len(metadata) >= 3:
                bed_start = f"{int(metadata[1])+1}"
                bed_end = metadata[2]
                (ref_allele, alt_allele, *clinvar_data) = metadata[3].split(";")
                if alt == alt_allele and (
                    bed_start == row_start and bed_end == row_end
                ):
                    new_row = in_row + [
                        urllib.parse.unquote(item) for item in clinvar_data
                    ]
                    results.append(new_row)
                    # is_matched = True
        # if not is_matched:
        #     in_row[2] = loc
        #     new_row = in_row + ["-", "-", "-", "-", "-", "-", "-"]
        #     results.append(new_row)
    return results


def lambda_handler(event, _):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]
    chrom_mapping = message["mapping"]
    request_id = message["requestId"]

    try:
        rows = [row.split("\t") for row in sns_data.split("\n") if row]
        new_rows = add_clinvar_columns(rows, chrom_mapping)
        base_filename = orchestrator.temp_file_name
        sns_data = "\n".join("\t".join(row) for row in new_rows)
        # start_function(
        #     topic_arn=PLUGIN_SIFT_SNS_TOPIC_ARN,
        #     base_filename=base_filename,
        #     message={
        #         "snsData": sns_data,
        #         "mapping": chrom_mapping,
        #     },
        # )
        # TODO Delete upload result function to SVEP_REGIONS (Latest plugin will upload the result)
        filename = f"/tmp/{base_filename}.tsv"
        with open(filename, "w") as tsv_file:
            tsv_file.write(sns_data)
        s3.Bucket(SVEP_REGIONS).upload_file(filename, f"{base_filename}.tsv")
        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
