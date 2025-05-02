import os


from shared.utils import (
    CheckedProcess,
    Orchestrator,
    download_bedfile,
    handle_failed_execution,
    start_function,
)

# Environment variables
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
CLINVAR_REFERENCE = os.environ["CLINVAR_REFERENCE"]
PLUGIN_GNOMAD_SNS_TOPIC_ARN = os.environ["PLUGIN_GNOMAD_SNS_TOPIC_ARN"]
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
    all_pos_rows = defaultdict(list)
    for in_row in in_rows:
        all_pos_rows[in_row["posVcf"]].append(in_row)
    for pos, pos_rows in all_pos_rows.items():
        args = [
            "tabix",
            f"/tmp/{CLINVAR_REFERENCE}",
            f"{ref_chrom}:{pos}-{pos}",
        ]
        query_process = CheckedProcess(args)
        main_data = query_process.stdout.read().rstrip("\n").split("\n")
        query_process.check()
        for in_row in pos_rows:
            ref = in_row["refVcf"]
            alt = in_row["altVcf"]
            is_matched = False
            for data in main_data:
                if not data:
                    continue
                _, bed_start, _, bed_ref, bed_alt, *clinvar_data = data.split("\t")
                if bed_alt == alt and bed_ref == ref and int(bed_start) + 1 == pos:
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
        f"Matched {num_rows_hit}/{len(in_rows)} rows to Clinvar, for a total of {len(results)} rows"
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
        if sns_data:
            start_function(
                topic_arn=PLUGIN_GNOMAD_SNS_TOPIC_ARN,
                base_filename=base_filename,
                message={
                    "snsData": sns_data,
                    "refChrom": ref_chrom,
                    "requestId": request_id,
                },
            )
        else:
            "No rows matched in clinvar, not continuing downstream plugins."
        orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
