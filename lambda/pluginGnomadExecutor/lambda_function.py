import json
import os
import subprocess

from shared.utils import (
    Orchestrator,
    handle_failed_execution,
    decompress_sns_data,
    compress_sns_data,
    get_sns_event,
    start_function,
)


GNOMAD_PUBLIC_CHR1 = os.environ["GNOMAD_PUBLIC_CHR1"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
PLUGIN_GNOMAD_SNS_TOPIC_ARN = os.environ["PLUGIN_GNOMAD_SNS_TOPIC_ARN"]
PLUGIN_GNOMAD_EXECUTOR_SNS_TOPIC_ARN = os.environ[
    "PLUGIN_GNOMAD_EXECUTOR_SNS_TOPIC_ARN"
]

base_url = "https://gnomad-public-us-east-1.s3.amazonaws.com"
vcf_key = "release/4.1/vcf/genomes/gnomad.genomes.v4.1.sites.chr11.vcf.bgz"


def get_query_process(chrom, start, end):
    # Ensure chromosome is prefixed correctly
    if not chrom.startswith("chr"):
        chrom = f"chr{chrom}"

    vcf_url = (
        f"{base_url}/release/4.1/vcf/genomes/gnomad.genomes.v4.1.sites.{chrom}.vcf.bgz"
    )

    args = [
        "bcftools",
        "query",
        "--regions",
        f"{chrom}:{start}-{end}",
        "--format",
        "%INFO/AF_afr\t%INFO/AF_eas\t%INFO/AF_fin\t%INFO/AF_nfe\t%INFO/AF_sas\t%INFO/AF_amr\t%INFO/AF\t%INFO/AC\t%INFO/AN\t%INFO/sift_max\n",
        vcf_url,
    ]

    print(f"[BCFTOOLS QUERY] {' '.join(args)}")

    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        cwd="/tmp",
    )

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"[ERROR] bcftools failed with code {process.returncode}")
        print(f"[STDERR] {stderr.strip()}")
        return []

    # Debug log if output is empty
    if not stdout.strip():
        print(f"[GNOMAD - INFO] No variant found in region {chrom}:{start}-{end}")

    return stdout.splitlines()


def add_gnomad_columns(in_rows, chrom_mapping, index):
    # Check if index is out of bounds
    if index >= len(in_rows):
        print(
            f"[GNOMAD - INFO] Index {index} out of bounds for in_rows length {len(in_rows)}"
        )
        return in_rows, index

    in_row = in_rows[index]
    chrom, positions = in_row[2].split(":")
    row_start, row_end = positions.split("-")
    alt = in_row[3]
    loc = f"{chrom_mapping.get(chrom, chrom)}:{positions}"

    print(f"[GNOMAD - INFO] running with chrom: {chrom}")

    region_lines = get_query_process(chrom, row_start, row_end)

    gnomad_info = ["."] * 10  # Default fallback values

    for line in region_lines:
        info_values = line.strip().split("\t")
        if len(info_values) == 10:
            gnomad_info = info_values
            break

    # Extend the row at the given index
    in_rows[index] = in_row + gnomad_info

    # If last index, keep it the same
    if index == len(in_rows) - 1:
        return in_rows, index
    else:
        return in_rows, index + 1


def lambda_handler(event, _):
    orchestrator = Orchestrator(event)

    message = get_sns_event(event)
    sns_data = message["snsData"]
    chrom_mapping = message["mapping"]
    request_id = message["requestId"]
    sns_index = message["snsIndex"]
    last_index = message["lastIndex"]

    print(f"[GNOMAD - INFO] sns_index: {sns_index}")
    print(f"[GNOMAD - INFO] last_index: {last_index}")

    print(f"[Gnomad] Request ID: {request_id}")
    try:
        sns_data = decompress_sns_data(sns_data)
        print(f"[GNOMAD - INFO] sns_data: {json.dumps(sns_data)}")

        rows = [row.split("\t") for row in sns_data.split("\n") if row]
        print(f"[GNOMAD - INFO] rows last_index: {last_index}")

        new_rows, next_index = add_gnomad_columns(rows, chrom_mapping, sns_index)
        sns_data = "\n".join("\t".join(row) for row in new_rows)
        compressed_sns_data = compress_sns_data(sns_data)
        base_filename = orchestrator.temp_file_name

        if sns_index == last_index:
            # Finish execution when it's last index
            print("[GNOMAD - INFO] Finished execution and upload to s3 Svep Region")
            base_filename = orchestrator.temp_file_name

            start_function(
                topic_arn=PLUGIN_GNOMAD_SNS_TOPIC_ARN,
                base_filename=base_filename,
                message={
                    "snsData": compressed_sns_data,
                    "mapping": chrom_mapping,
                    "requestId": request_id,
                    "isCompleted": True,
                },
            )

        else:
            # Re running lambda function with next index
            print(f"[GNOMAD - INFO] re running lambda with next_index: {next_index}")
            compressed_sns_data = compress_sns_data(sns_data)

            start_function(
                topic_arn=PLUGIN_GNOMAD_EXECUTOR_SNS_TOPIC_ARN,
                base_filename=base_filename,
                message={
                    "snsData": compressed_sns_data,
                    "mapping": chrom_mapping,
                    "requestId": request_id,
                    "snsIndex": next_index,
                    "lastIndex": last_index,
                },
            )

        orchestrator.mark_completed()

    except Exception as e:
        handle_failed_execution(request_id, e)
