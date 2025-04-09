import json
import os
import subprocess

from shared.utils import (
    Orchestrator,
    s3,
    handle_failed_execution,
    decompress_sns_data,
)


GNOMAD_PUBLIC_CHR1 = os.environ["GNOMAD_PUBLIC_CHR1"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]

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
        print(f"[INFO] No variant found in region {chrom}:{start}-{end}")

    return stdout.splitlines()


def add_gnomad_columns(in_rows, chrom_mapping):
    num_rows_hit = 0

    print(f"[gnomad in_rows]: {in_rows}")

    results = []

    for in_row in in_rows:
        chrom, positions = in_row[2].split(":")
        row_start, row_end = positions.split("-")
        alt = in_row[3]
        loc = f"{chrom_mapping.get(chrom, chrom)}:{positions}"

        region_lines = get_query_process(chrom, row_start, row_end)

        # Default to placeholder values if nothing matched
        gnomad_info = ["."] * 10

        for line in region_lines:
            print(f"[gnomad line]: {line}")
            # Assuming region_lines is a list of tab-separated values
            info_values = line.strip().split("\t")
            if len(info_values) == 10:
                gnomad_info = info_values
                num_rows_hit += 1
                break

        # Append gnomad_info to the original row
        extended_row = in_row + gnomad_info
        results.append(extended_row)

    return results


def lambda_handler(event, _):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]
    chrom_mapping = message["mapping"]
    request_id = message["requestId"]

    print(f"[Gnomad] Request ID: {request_id}")

    sns_data = decompress_sns_data(sns_data)

    try:
        rows = [row.split("\t") for row in sns_data.split("\n") if row]

        new_rows = add_gnomad_columns(rows, chrom_mapping)

        base_filename = orchestrator.temp_file_name
        sns_data = "\n".join("\t".join(row) for row in new_rows)

        print(f"[Gnomad] SNS Data: {json.dumps(sns_data)}")

        filename = f"/tmp/{base_filename}.tsv"
        with open(filename, "w") as tsv_file:
            tsv_file.write(sns_data)
        s3.Bucket(SVEP_REGIONS).upload_file(filename, f"{base_filename}.tsv")
        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
