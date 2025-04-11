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
    Timer,
)

SVEP_REGIONS = os.environ["SVEP_REGIONS"]
PLUGIN_GNOMAD_SNS_TOPIC_ARN = os.environ["PLUGIN_GNOMAD_SNS_TOPIC_ARN"]
MILLISECONDS_BEFORE_SPLIT = 4000
base_url = "https://gnomad-public-us-east-1.s3.amazonaws.com"


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


def add_gnomad_columns(in_rows, ref_chrom, index):
    # Check if index is out of bounds
    if index >= len(in_rows):
        print(
            f"[GNOMAD - INFO] Index {index} out of bounds for in_rows length {len(in_rows)}"
        )
        return in_rows, index

    in_row = in_rows[index]
    chrom, positions = in_row[2].split(":")
    row_start, row_end = positions.split("-")

    print(f"[GNOMAD - INFO] running with chrom: {ref_chrom}")

    region_lines = get_query_process(ref_chrom, row_start, row_end)

    gnomad_info = ["."] * 10

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


def lambda_handler(event):
    orchestrator = Orchestrator(event)
    message = orchestrator.message

    sns_data = message["snsData"]
    request_id = message["requestId"]
    ref_chrom = message["refChrom"]
    sns_index = message["snsIndex"]

    print(f"[Gnomad] Request ID: {request_id}")

    try:
        sns_data = decompress_sns_data(sns_data)
        print(f"[GNOMAD - INFO] sns_data: {json.dumps(sns_data)}")

        rows = [row.split("\t") for row in sns_data.split("\n") if row]

        new_rows, next_index = add_gnomad_columns(rows, ref_chrom, sns_index)
        sns_data = "\n".join("\t".join(row) for row in new_rows)
        compressed_sns_data = compress_sns_data(sns_data)
        base_filename = orchestrator.temp_file_name

        # last_index = len(rows) - 1
        last_index = 2

        if sns_index == last_index:
            # Finish execution when it's last index
            print(f"[GNOMAD - INFO] Completed")

            filename = f"/tmp/{base_filename}.tsv"
            with open(filename, "w") as tsv_file:
                tsv_file.write(sns_data)
            s3.Bucket(SVEP_REGIONS).upload_file(filename, f"{base_filename}.tsv")
        else:
            # Re running lambda function with next index
            print(f"[GNOMAD - INFO] re running lambda with next_index: {next_index}")
            compressed_sns_data = compress_sns_data(sns_data)
            start_function(
                topic_arn=PLUGIN_GNOMAD_SNS_TOPIC_ARN,
                base_filename=base_filename,
                message={
                    "snsData": compressed_sns_data,
                    "requestId": request_id,
                    "snsIndex": next_index,
                    "lastIndex": last_index,
                    "refChrom": ref_chrom,
                    # "lastIndex": last_index,
                },
                resend=True,
            )

        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
