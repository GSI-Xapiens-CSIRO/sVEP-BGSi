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
PLUGIN_GNOMAD_ONE_KG_SNS_TOPIC_ARN = os.environ["PLUGIN_GNOMAD_ONE_KG_SNS_TOPIC_ARN"]  # reuse or rename
# Change to appropriate 1KG location
KGENOMES_S3_PREFIX = "https://1000genomes.s3.amazonaws.com/release/20130502/"
KGENOMES_S3_SUFFIX = ".vcf.gz"

MAX_REGIONS_PER_QUERY = 20
MILLISECONDS_BEFORE_SPLIT = 300000

# Adjust these to actual INFO fields available in 1KG files
KGENOMES_COLUMNS = {
    "af": "INFO/AF",
    "ac": "INFO/AC",
    "an": "INFO/AN"
}

def get_query_process(regions, ref_chrom):
    chrom = f"chr{ref_chrom}"  # or just use the number if 1KG doesn't use 'chr'
    vcf_url = f"{KGENOMES_S3_PREFIX}ALL.{ref_chrom}.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes{KGENOMES_S3_SUFFIX}"
    args = [
        "bcftools",
        "query",
        "--regions",
        ",".join(f"{chrom}:{region}" for region in regions),
        "--format",
        f"%POS\t%REF\t%ALT\t{'\\t'.join('%' + val for val in KGENOMES_COLUMNS.values())}\n",
        vcf_url,
    ]
    return CheckedProcess(args, error_message="bcftools error querying 1000 Genomes")


def convert_to_regions_queries(sns_data):
    regions_data = defaultdict(lambda: defaultdict(list))
    for data in sns_data:
        regions_data[data["posVcf"]][(data["refVcf"], data["altVcf"])].append(data)
    regions_list = sorted(list(regions_data.keys()))
    region_chunks = [
        regions_list[i : i + MAX_REGIONS_PER_QUERY]
        for i in range(0, len(regions_list), MAX_REGIONS_PER_QUERY)
    ]
    chunked_data = [
        {
            (pos, ref, alt): data_value
            for pos in region_chunk
            for (ref, alt), data_value in regions_data[pos].items()
        }
        for region_chunk in region_chunks
    ]
    return region_chunks, chunked_data


def add_1kg_columns(sns_data, ref_chrom, timer):
    region_queries, chunked_data = convert_to_regions_queries(sns_data)
    query_processes = [
        get_query_process(query_region, ref_chrom) for query_region in region_queries
    ]
    lines_updated = 0
    completed_lines = []
    remaining_data = []
    for query_process, (chunk_i, regions_data) in zip(
        query_processes, enumerate(chunked_data)
    ):
        if timer.out_of_time():
            remaining_data = [
                data
                for later_region_data in chunked_data[chunk_i:]
                for variant_data in later_region_data.values()
                for data in variant_data
            ]
            break
        for line in query_process.stdout:
            line = line.strip()
            if not line:
                continue
            pos_s, ref, alt, *query_data = line.split("\t")
            pos = int(pos_s)
            if (pos, ref, alt) not in regions_data:
                continue
            for data in regions_data[(pos, ref, alt)]:
                data.update(
                    {
                        col_name: kgenomes_datum
                        for col_name, kgenomes_datum in zip(
                            list(KGENOMES_COLUMNS.keys()), query_data
                        )
                    }
                )
                lines_updated += 1
        completed_lines.extend(
            [data for variant_data in regions_data.values() for data in variant_data]
        )
        query_process.check()
    print(f"Updated {lines_updated}/{len(completed_lines)} rows with 1000 Genomes data")
    return completed_lines, remaining_data


def lambda_handler(event, context):
    timer = Timer(context, MILLISECONDS_BEFORE_SPLIT)
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]
    ref_chrom = message["refChrom"]
    request_id = message["requestId"]

    try:
        complete_lines, remaining = add_1kg_columns(sns_data, ref_chrom, timer)
        if remaining:
            print(f"remaining data length {len(remaining)}")
            start_function(
                topic_arn=PLUGIN_GNOMAD_ONE_KG_SNS_TOPIC_ARN,
                base_filename=orchestrator.temp_file_name,
                message={
                    "snsData": remaining,
                    "refChrom": ref_chrom,
                    "requestId": request_id,
                },
                resend=True,
            )
            assert (
                len(complete_lines) > 0
            ), "Not able to make any progress getting 1KG data"
        start_function(
            topic_arn=FORMAT_OUTPUT_SNS_TOPIC_ARN,
            base_filename=orchestrator.temp_file_name,
            message={
                "snsData": complete_lines,
                "requestId": request_id,
            },
        )
        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)