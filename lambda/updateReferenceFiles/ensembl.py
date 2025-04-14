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
GTF_BASE = os.environ["GTF_BASE"]
SPLICE_BASE = os.environ["SPLICE_BASE"]
FASTA_BASE = os.environ["FASTA_BASE"]


def update_ensembl(ensembl_version):
    ensembl_gtf_url = f"https://ftp.ensembl.org/pub/release-{ensembl_version}/gtf/homo_sapiens/Homo_sapiens.GRCh38.{ensembl_version}.chr.gtf.gz"
    sns_publish(
        UPDATEREFERENCEFILES_SNS_TOPIC_ARN,
        {"file_url": ensembl_gtf_url, "file_type": "ensembl_gtf"},
    )
    print(f"Published GTF update for version {ensembl_version}.")

    chromosomes = list(map(str, range(1, 23))) + ["X", "Y", "MT"]
    for chr in chromosomes:
        ensembl_fasta_url = f"https://ftp.ensembl.org/pub/release-{ensembl_version}/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.chromosome.{chr}.fa.gz"
        sns_publish(
            UPDATEREFERENCEFILES_SNS_TOPIC_ARN,
            {"file_url": ensembl_fasta_url, "file_type": "ensembl_fasta", "chr": chr},
        )
        print(
            f"Published FASTA update for version {ensembl_version} and chromsome {chr}."
        )

    update_references_table(
        id="ensembl_version",
        version=ensembl_version,
    )


def process_ensembl_gtf(gtf_url):
    gtf_file = prepend_tmp(f"{GTF_BASE}.gtf")
    gzipped_gtf_file = prepend_tmp(f"{gtf_file}.gz")
    download_remote_content(gtf_url, gzipped_gtf_file)

    # GTF
    _gunzip(gzipped_gtf_file, gtf_file)
    _remove(gzipped_gtf_file)

    filtered_gtf_file = prepend_tmp(f"filtered_{gtf_file}")
    _filter(gtf_file, filtered_gtf_file, "gene")

    # GTF
    sorted_filtered_gtf_file = prepend_tmp(f"sorted_{filtered_gtf_file}")
    _sort(filtered_gtf_file, sorted_filtered_gtf_file)
    _remove(filtered_gtf_file)

    bgzipped_gtf_file = prepend_tmp(f"{sorted_filtered_gtf_file}.bgz")
    _bgzip(sorted_filtered_gtf_file, bgzipped_gtf_file)

    bgzipped_gtf_index = prepend_tmp(f"{bgzipped_gtf_file}.tbi")
    _tabix_index(bgzipped_gtf_file)

    # SPLICE
    splice_file = prepend_tmp(f"{SPLICE_BASE}.gtf")
    _extract_splice(sorted_filtered_gtf_file, splice_file)
    _remove(sorted_filtered_gtf_file)

    sorted_splice_file = prepend_tmp(f"sorted_{splice_file}")
    _sort(splice_file, sorted_splice_file)
    _remove(splice_file)

    bgzipped_splice_file = prepend_tmp(f"{sorted_splice_file}.bgz")
    _bgzip(sorted_splice_file, bgzipped_splice_file)
    _remove(sorted_splice_file)

    bgzipped_splice_index = prepend_tmp(f"{bgzipped_splice_file}.tbi")
    _tabix_index(bgzipped_splice_file)

    files = [
        bgzipped_gtf_file,
        bgzipped_gtf_index,
        bgzipped_splice_file,
        bgzipped_splice_index,
    ]
    keys = list(map(lambda file: truncate_tmp(file), files))

    s3_upload(
        bucket=REFERENCE_LOCATION,
        keys=keys,
        files=files,
    )


def process_ensembl_fasta(fasta_url, chr):
    fasta_file = prepend_tmp(f"{FASTA_BASE}.{chr}.fa")
    gzipped_fasta_file = prepend_tmp(f"{fasta_file}.gz")
    download_remote_content(fasta_url, gzipped_fasta_file)

    _gunzip(gzipped_fasta_file, fasta_file)
    _remove(gzipped_fasta_file)

    bgzipped_fasta = prepend_tmp(f"{fasta_file}.bgz")
    _bgzip(fasta_file, bgzipped_fasta)
    _remove(fasta_file)

    fai_indexed_fasta = prepend_tmp(f"{bgzipped_fasta}.fai")
    gzi_indexed_fasta = prepend_tmp(f"{bgzipped_fasta}.gzi")
    _faidx_index(bgzipped_fasta)

    files = [
        bgzipped_fasta,
        fai_indexed_fasta,
        gzi_indexed_fasta,
    ]
    keys = list(map(lambda file: truncate_tmp(file), files))

    s3_upload(
        bucket=REFERENCE_LOCATION,
        keys=keys,
        files=files,
    )


def _gunzip(input_file, output_file):
    command = f"gunzip -c {input_file} > {output_file}"
    execute_subprocess(command)


def _extract_splice(input_file, output_file):
    command = f'awk -F\'[" \t]\' \'{{print $1"\t"$2"\t"$3"\t"$4"\t"$5"\t"$6"\t"$7"\t"$19}}\' {input_file} > {output_file}'
    execute_subprocess(command)


def _faidx_index(input_file):
    command = f"samtools faidx {input_file}"
    execute_subprocess(command)
