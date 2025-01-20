import os

from shared.utils import (
    download_remote_content,
    execute_subprocess,
    prepend_tmp,
    sns_publish,
    s3_upload,
    truncate_tmp,
    update_references_table,
    _remove,
    _filter,
    _sort,
    _bgzip,
    _tabix_index,
)

REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]
UPDATEREFERENCEFILES_SNS_TOPIC_ARN = os.environ["UPDATEREFERENCEFILES_SNS_TOPIC_ARN"]
MIRNA_BASE = os.environ["MIRNA_BASE"]


def update_mirna(mirna_hash):
    mirna_gff3_url = "https://www.mirbase.org/download/hsa.gff3"
    sns_publish(
        UPDATEREFERENCEFILES_SNS_TOPIC_ARN,
        {"file_url": mirna_gff3_url, "file_type": "mirna_gff"},
    )
    print(f"Published miRNA gff3 update due to a hash change.")

    update_references_table(
        id="mirna_hash",
        version=mirna_hash,
    )


def process_mirna_gff(mirna_url):
    mirna_file = prepend_tmp(f"{MIRNA_BASE}.gff3")
    download_remote_content(mirna_url, mirna_file)

    filtered_mirna_file = prepend_tmp(f"filtered_{mirna_file}")
    _filter(mirna_file, filtered_mirna_file, "miRNA_primary_transcript")
    _remove(mirna_file)

    second_filtered_mirna_file = prepend_tmp(f"second_{filtered_mirna_file}")
    _second_mirna_filter(filtered_mirna_file, second_filtered_mirna_file)
    _remove(filtered_mirna_file)

    sorted_filtered_mirna_file = prepend_tmp(f"sorted_filtered_{mirna_file}")
    _sort(second_filtered_mirna_file, sorted_filtered_mirna_file)
    _remove(second_filtered_mirna_file)

    bgzipped_mirna_file = prepend_tmp(f"{sorted_filtered_mirna_file}.bgz")
    _bgzip(sorted_filtered_mirna_file, bgzipped_mirna_file)
    _remove(sorted_filtered_mirna_file)

    bgzipped_mirna_index = prepend_tmp(f"{bgzipped_mirna_file}.tbi")
    _tabix_index(bgzipped_mirna_file)

    files = [
        bgzipped_mirna_file,
        bgzipped_mirna_index,
    ]
    keys = list(map(lambda file: truncate_tmp(file), files))

    s3_upload(
        bucket=REFERENCE_LOCATION,
        keys=keys,
        files=files,
    )


def _second_mirna_filter(input_file, output_file):
    command = f"""awk -F '\t' '{{ print $1"\t"$2"\t"$3"\t"$4"\t"$5"\t"$6"\t"$7 }}' {input_file} > {output_file}"""
    execute_subprocess(command)
