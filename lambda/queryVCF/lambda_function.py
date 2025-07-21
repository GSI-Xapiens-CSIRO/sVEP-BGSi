import os

from shared.utils import (
    CheckedProcess,
    orchestration,
    Timer,
)


# Environment variables
FILTER_MIN_QUAL = float(os.environ["FILTER_MIN_QUAL"])
QUERY_VCF_SUBMIT_SNS_TOPIC_ARN = os.environ["QUERY_VCF_SUBMIT_SNS_TOPIC_ARN"]
SLICE_SIZE_MBP = int(os.environ["SLICE_SIZE_MBP"])
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

MILLISECONDS_BEFORE_SPLIT = 130000
MILLISECONDS_BEFORE_SECOND_SPLIT = 120000
RECORDS_PER_SAMPLE = 700
BATCH_CHUNK_SIZE = 20
PAYLOAD_SIZE = 260000

REQUESTED_FORMAT_TAGS = {
    "gt": "GT",
    "dp": "DP",
    "gq": "GQ",
    "mq": "MQ",
    "qd": "QD",
}


def get_info_format_tags(location):
    args = [
        "bcftools",
        "head",
        location,
    ]
    process = CheckedProcess(args)
    info_tags = set()
    format_tags = set()
    for line in process.stdout:
        if line.startswith("##INFO=<ID="):
            info_tags.add(line.split("ID=")[1].split(",")[0])
        elif line.startswith("##FORMAT=<ID="):
            format_tags.add(line.split("ID=")[1].split(",")[0])
    process.check()
    print("Found INFO tags:", info_tags)
    print("Found FORMAT tags:", format_tags)
    return info_tags, format_tags


def get_db_tags(tags):
    db_tags = "|".join(
        f"%INFO/{tag}"
        for tag in [
            "ONCDISDBINCL",
            "CLNDISDB",
            "CLNDISDBINCL",
            "SCIDISDBINCL",
        ]
        if tag in tags
    )
    return db_tags


def get_query_fields(location):
    info_tags, format_tags = get_info_format_tags(location)
    db_tags = get_db_tags(info_tags)
    return {
        "chrom": "%CHROM",
        "posVcf": "%POS",
        "refVcf": "%REF",
        "altVcf": "%ALT",
        "qual": "%QUAL",
        "filter": "%FILTER",
        **({"dbIds": db_tags} if db_tags else {}),
        **{
            field: f"[%{tag}]"
            for field, tag in REQUESTED_FORMAT_TAGS.items()
            if tag in format_tags
        },
    }


def get_query_lines(location, chrom, start, end, query_values):
    norm_args = [
        "bcftools",
        "norm",
        "--regions",
        f"{chrom}:{start}-{end}",
        "--atomize",
        "--atom-overlaps",
        ".",
        "--multiallelics",
        "-both",
        location,
    ]
    norm_process = CheckedProcess(norm_args)
    query_args = [
        "bcftools",
        "query",
        "--format",
        "\t".join(query_values) + "\n",
    ]
    query_process = CheckedProcess(query_args, stdin=norm_process.stdout)
    lines = query_process.stdout.read().splitlines()
    norm_process.check()
    query_process.check()
    return lines


def trim_alleles(vcf_line_dict):
    pos = int(vcf_line_dict["posVcf"])
    ref = vcf_line_dict["refVcf"]
    alt = vcf_line_dict["altVcf"]
    while len(ref) > 1 and len(alt) > 1:
        if ref[-1] == alt[-1]:
            ref = ref[:-1]
            alt = alt[:-1]
        elif ref[0] == alt[0]:
            ref = ref[1:]
            alt = alt[1:]
            pos += 1
        else:
            break
    vcf_line_dict.update(
        {
            "posVcf": pos,
            "refVcf": ref,
            "altVcf": alt,
        }
    )
    return vcf_line_dict


def submit_query_gtf(orc, regions_list, base_id, timer, query_keys):
    all_lines = [
        trim_alleles(
            {
                key: value
                for key, value in zip(
                    query_keys,
                    vcf_line.split("\t"),
                )
            }
        )
        for vcf_line in regions_list
    ]
    # Filter out records with low quality
    before_filter = len(all_lines)
    passed_lines = [
        line_dict
        for line_dict in all_lines
        if ((qual := line_dict["qual"]) == ".") or (float(qual) >= FILTER_MIN_QUAL)
    ]
    print(
        f"Passed {len(passed_lines)}/{before_filter} records with QUAL >= {FILTER_MIN_QUAL} or unknown"
    )
    total_coords = [
        passed_lines[x : x + RECORDS_PER_SAMPLE]
        for x in range(0, len(passed_lines), RECORDS_PER_SAMPLE)
    ]
    for idx in range(len(total_coords)):
        idx_base_id = f"{base_id}_{idx}"
        if timer.out_of_time():
            # Call self with remaining data
            remaining_coords = total_coords[idx:]
            print(f"remaining coords length {len(remaining_coords)}")
            # These payloads will likely trigger s3 uploads, but it's faster than splitting into
            # smaller chunks and starting more smaller functions.
            for i in range(0, len(remaining_coords), BATCH_CHUNK_SIZE):
                orc.start_function(
                    topic_arn=QUERY_VCF_SUBMIT_SNS_TOPIC_ARN,
                    suffix=idx_base_id,
                    message={
                        "coords": remaining_coords[i : i + BATCH_CHUNK_SIZE],
                    },
                    track=True,
                )
            break
        else:
            orc.next_function(
                suffix=idx_base_id,
                message={
                    "coords": total_coords[idx],
                },
            )


def lambda_handler(event, context):
    first_timer = Timer(context, MILLISECONDS_BEFORE_SPLIT)
    second_timer = Timer(context, MILLISECONDS_BEFORE_SECOND_SPLIT)
    with orchestration(event) as orc:
        message = orc.message
        vcf_regions = message["regions"]
        location = message["location"]
        query_fields = get_query_fields(location)
        print(f"query fields: {query_fields}")
        chrom_mapping = message["mapping"]
        for index, region in enumerate(vcf_regions):
            if first_timer.out_of_time():
                new_regions = vcf_regions[index:]
                print(f"New Regions {new_regions}")
                # Publish SNS for itself!
                orc.resend_self(
                    message_update={
                        "regions": new_regions,
                    },
                )
                break
            else:
                chrom, start_str = region.split(":")
                orc.ref_chrom = chrom_mapping[chrom]
                region_base_id = f"{chrom}_{start_str}"
                start = round(1000000 * float(start_str) + 1)
                end = start + round(1000000 * SLICE_SIZE_MBP - 1)
                query_lines = get_query_lines(
                    location, chrom, start, end, query_fields.values()
                )
                submit_query_gtf(
                    orc, query_lines, region_base_id, second_timer, query_fields.keys()
                )
