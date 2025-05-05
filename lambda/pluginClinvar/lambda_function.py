import os
from collections import defaultdict


from shared.utils import (
    CheckedProcess,
    orchestration,
    download_bedfile,
)

# Environment variables
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
CLINVAR_REFERENCE = os.environ["CLINVAR_REFERENCE"]
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
FILTER_CLINVAR_EXCLUDE = set(os.environ["FILTER_CLINVAR_EXCLUDE"].split(",")) - {""}

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
    # Filter out rows that are not clinically significant
    passed_results = [
        result for result in results if result["clinSig"] not in FILTER_CLINVAR_EXCLUDE
    ]
    print(
        f"Passed {len(passed_results)}/{len(results)} records with clinSig not in {FILTER_CLINVAR_EXCLUDE}"
    )
    return passed_results


def lambda_handler(event, _):
    with orchestration(event) as orc:
        sns_data = orc.message["snsData"]
        sns_data = add_clinvar_columns(sns_data, orc.ref_chrom)
        if sns_data:
            orc.next_function(
                message={
                    "snsData": sns_data,
                },
            )
        else:
            "No rows matched in clinvar, not continuing downstream plugins."
