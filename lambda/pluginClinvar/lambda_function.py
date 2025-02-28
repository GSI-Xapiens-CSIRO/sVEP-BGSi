import os

from shared.utils import Orchestrator, s3


# Environment variables
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'


def add_clinvar_columns(in_rows, chrom_mapping):
    pass


def lambda_handler(event, _):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]
    chrom_mapping = message["mapping"]
    rows = [
        row.split("\t")
        for row in sns_data.split("\n")
        if row
    ]
    add_clinvar_columns(rows, chrom_mapping)
    base_filename = orchestrator.temp_file_name
    filename = f"/tmp/{base_filename}.tsv"
    with open(filename, "w") as tsv_file:
        print("\n".join("\t".join(row) for row in rows), file=tsv_file)
    s3.Bucket(SVEP_REGIONS).upload_file(filename, f"{base_filename}.tsv")
    print("uploaded")
    orchestrator.mark_completed()
