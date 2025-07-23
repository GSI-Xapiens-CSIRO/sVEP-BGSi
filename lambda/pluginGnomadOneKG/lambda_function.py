from collections import defaultdict

from shared.utils import (
    CheckedProcess,
    orchestration,
    Timer,
)

GNOMAD_S3_PREFIX = "https://gnomad-public-us-east-1.s3.amazonaws.com/release/3.1.2/vcf/genomes/gnomad.genomes.v3.1.2.hgdp_tgp."
GNOMAD_S3_SUFFIX = ".vcf.bgz"

MAX_REGIONS_PER_QUERY = 20
MILLISECONDS_BEFORE_SPLIT = 300000

KGENOMES_COLUMNS = {
    "af1KG": "INFO/AF",
    "afKhv": "INFO/AF_khv",
    "ac1KG": "INFO/AC",
    "an1KG": "INFO/AN",
}


def get_query_process(regions, ref_chrom):
    chrom = f"chr{ref_chrom}"
    args = [
        "bcftools",
        "query",
        "--regions",
        ",".join(f"{chrom}:{region}" for region in regions),
        "--format",
        f"%POS\t%REF\t%ALT\t{'\\t'.join('%' + val for val in KGENOMES_COLUMNS.values())}\n",
        f"{GNOMAD_S3_PREFIX}{chrom}{GNOMAD_S3_SUFFIX}",
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
    with orchestration(event) as orc:
        sns_data = orc.message["snsData"]
        complete_lines, remaining = add_1kg_columns(sns_data, orc.ref_chrom, timer)
        if remaining:
            print(f"remaining data length {len(remaining)}")
            orc.resend_self(
                message_update={
                    "snsData": remaining,
                },
            )
            assert len(remaining) < len(
                sns_data
            ), "Not able to make any progress getting gnomAD data"
        orc.next_function(
            message={
                "snsData": complete_lines,
            },
        )
