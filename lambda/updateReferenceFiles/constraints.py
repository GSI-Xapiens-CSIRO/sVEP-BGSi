import json
import os

from shared.utils import (
    download_remote_content,
    prepend_tmp,
    sns_publish,
    s3_upload,
    truncate_tmp,
    update_references_table,
)

REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]
UPDATEREFERENCEFILES_SNS_TOPIC_ARN = os.environ["UPDATEREFERENCEFILES_SNS_TOPIC_ARN"]


def update_constraints(gnomad_version):
    sns_publish(
        UPDATEREFERENCEFILES_SNS_TOPIC_ARN,
        {"gnomad_version": gnomad_version, "file_type": "gnomad_constraints"},
    )
    print(f"Published gnomad constraints update due to different version.")


def process_constraints(gnomad_version):
    constraints_url = f"https://gnomad-public-us-east-1.s3.amazonaws.com/release/{gnomad_version}/constraint/gnomad.v{gnomad_version}.constraint_metrics.tsv"
    constraints_filename = prepend_tmp("gnomad_constraint_metrics.tsv")
    download_remote_content(constraints_url, constraints_filename)
    pos = 0
    last_gene = None
    index = {}
    with open(constraints_filename) as constraints_file:
        while line := constraints_file.readline():
            gene = line.split("\t")[0]
            if gene != last_gene:
                index[gene] = pos
                last_gene = gene
            pos = constraints_file.tell()
    index_filename = f"{constraints_filename}.idx"
    with open(index_filename, "w") as constraints_index_file:
        json.dump(index, constraints_index_file)
    s3_upload(
        bucket=REFERENCE_LOCATION,
        keys=[
            truncate_tmp(constraints_filename),
            truncate_tmp(index_filename),
        ],
        files=[
            constraints_filename,
            index_filename,
        ],
    )
    update_references_table(
        id="gnomad_constraints_version",
        version=gnomad_version,
    )
