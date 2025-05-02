import os

from shared.utils import (
    CheckedProcess,
    orchestration,
    Timer,
)


# Environment variables
QUERY_GTF_SNS_TOPIC_ARN = os.environ["QUERY_GTF_SNS_TOPIC_ARN"]
QUERY_VCF_SUBMIT_SNS_TOPIC_ARN = os.environ["QUERY_VCF_SUBMIT_SNS_TOPIC_ARN"]
SLICE_SIZE_MBP = int(os.environ["SLICE_SIZE_MBP"])
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

MILLISECONDS_BEFORE_SPLIT = 15000
MILLISECONDS_BEFORE_SECOND_SPLIT = 6000
RECORDS_PER_SAMPLE = 700
BATCH_CHUNK_SIZE = 10
PAYLOAD_SIZE = 260000

QUERY_KEYS = [
    "chrom",
    "posVcf",
    "refVcf",
    "altVcf",
    "qual",
    "filter",
    "gt",
]


def get_query_lines(location, chrom, start, end):
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
        "%CHROM\t%POS\t%REF\t%ALT\t%QUAL\t%FILTER\t[%GT]\n",
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


def submit_query_gtf(orc, regions_list, base_id, timer):
    total_coords = [
        [
            trim_alleles(
                {
                    key: value
                    for key, value in zip(
                        QUERY_KEYS,
                        vcf_line.split("\t"),
                    )
                }
            )
            for vcf_line in regions_list[x : x + RECORDS_PER_SAMPLE]
        ]
        for x in range(0, len(regions_list), RECORDS_PER_SAMPLE)
    ]

    for idx in range(len(total_coords)):
        idx_base_id = f"{base_id}_{idx}"
        if timer.out_of_time():
            # Call self with remaining data
            remaining_coords = total_coords[idx:]
            print(f"remaining coords length {len(remaining_coords)}")
            # Since coords are generally similar size because it's
            # made of chr, loc, ref, alt - we know 10 batches of 700
            # records can be handled by SNS
            for i in range(0, len(remaining_coords), BATCH_CHUNK_SIZE):
                orc.start_function(
                    topic_arn=QUERY_VCF_SUBMIT_SNS_TOPIC_ARN,
                    suffix=idx_base_id,
                    message={
                        "coords": remaining_coords[i : i + BATCH_CHUNK_SIZE],
                    },
                )
            break
        else:
            orc.start_function(
                topic_arn=QUERY_GTF_SNS_TOPIC_ARN,
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
                query_lines = get_query_lines(location, chrom, start, end)
                submit_query_gtf(
                    orc,
                    query_lines,
                    region_base_id,
                    second_timer,
                )
