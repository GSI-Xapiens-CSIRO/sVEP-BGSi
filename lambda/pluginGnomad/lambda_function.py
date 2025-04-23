from collections import defaultdict
import os

from shared.utils import (
    CheckedProcess,
    Orchestrator,
    handle_failed_execution,
    start_function,
    Timer,
)

FORMAT_OUTPUT_SNS_TOPIC_ARN = os.environ["FORMAT_OUTPUT_SNS_TOPIC_ARN"]
PLUGIN_GNOMAD_SNS_TOPIC_ARN = os.environ["PLUGIN_GNOMAD_SNS_TOPIC_ARN"]
GNOMAD_S3_PREFIX = "https://gnomad-public-us-east-1.s3.amazonaws.com/release/4.1/vcf/genomes/gnomad.genomes.v4.1.sites."
GNOMAD_S3_SUFFIX = ".vcf.bgz"
MAX_REGIONS_PER_QUERY = 20  # Hard limit is probably around 5000
# Just the columns after the identifying columns
GNOMAD_COLUMNS = {
    "afAfr": "INFO/AF_afr",
    "afEas": "INFO/AF_eas",
    "afFin": "INFO/AF_fin",
    "afNfe": "INFO/AF_nfe",
    "afSas": "INFO/AF_sas",
    "afAmr": "INFO/AF_amr",
    "af": "INFO/AF",
    "ac": "INFO/AC",
    "an": "INFO/AN",
    "siftMax": "INFO/sift_max",
}
MILLISECONDS_BEFORE_SPLIT = 300000


def get_query_process(regions, ref_chrom):
    chrom = f"chr{ref_chrom}"
    args = [
        "bcftools",
        "query",
        "--regions",
        ",".join(f"{chrom}:{region}" for region in regions),
        "--format",
        f"%POS\t%REF\t%ALT\t{'\\t'.join("%" + val for val in GNOMAD_COLUMNS.values())}\n",
        f"{GNOMAD_S3_PREFIX}{chrom}{GNOMAD_S3_SUFFIX}",
    ]
    return CheckedProcess(args=args, error_message="bcftools error querying gnomAD")


def convert_to_regions_queries(sns_data):
    regions = set()
    for data in sns_data:
        positions = data["region"].split(":")[1]
        start, end = positions.split("-")
        regions.add(positions if start != end else start)
    # Split into chunks of MAX_REGIONS_PER_QUERY
    regions_list = sorted(list(regions), key=lambda x: int(x.split("-")[0]))
    region_chunks = [
        regions_list[i : i + MAX_REGIONS_PER_QUERY]
        for i in range(0, len(regions_list), MAX_REGIONS_PER_QUERY)
    ]
    return region_chunks


def add_gnomad_columns(sns_data, ref_chrom, timer):
    region_queries = convert_to_regions_queries(sns_data)
    query_processes_sns_data = [
        get_query_process(query_region, ref_chrom) for query_region in region_queries
    ]
    regions_data = defaultdict(list)
    for data in sns_data:
        regions_data[
            (data["region"].split(":")[1].split("-")[0], data["ref"], data["alt"])
        ].append(data)
    lines_updated = 0
    completed_lines = []
    for query_process in query_processes_sns_data:
        for line in query_process.stdout:
            line = line.strip()
            if not line:
                continue
            pos, ref, alt, *query_data = line.split("\t")
            if (pos, ref, alt) not in regions_data:
                continue
            for data in regions_data[(pos, ref, alt)]:
                data.update(
                    {
                        col_name: gnomad_datum
                        for col_name, gnomad_datum in zip(
                            list(GNOMAD_COLUMNS.keys()), query_data
                        )
                    }
                )
                completed_lines.append(data)
                lines_updated += 1
            del regions_data[(pos, ref, alt)]
            if timer.out_of_time():
                # Call self with remaining data
                remaining_data = [
                    data for pos_data in regions_data.values() for data in pos_data
                ]
                return completed_lines, remaining_data
        query_process.check()
    return sns_data, []


def lambda_handler(event, context):
    timer = Timer(context, MILLISECONDS_BEFORE_SPLIT)
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]
    ref_chrom = message["refChrom"]
    request_id = message["requestId"]

    try:
        complete_lines, remaining = add_gnomad_columns(sns_data, ref_chrom, timer)
        if remaining:
            print(f"remaining data length {len(remaining)}")
            start_function(
                topic_arn=PLUGIN_GNOMAD_SNS_TOPIC_ARN,
                base_filename=base_filename,
                message={
                    "snsData": remaining,
                    "refChrom": ref_chrom,
                    "requestId": request_id,
                },
                resend=True,
            )
            assert (
                len(complete_lines) > 0
            ), "Not able to make any progress getting gnomAD data"
        print(f"Updated {len(complete_lines)}/{len(sns_data)} rows with gnomad data")
        base_filename = orchestrator.temp_file_name
        start_function(
            topic_arn=FORMAT_OUTPUT_SNS_TOPIC_ARN,
            base_filename=base_filename,
            message={
                "snsData": complete_lines,
                "requestId": request_id,
            },
        )
        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
