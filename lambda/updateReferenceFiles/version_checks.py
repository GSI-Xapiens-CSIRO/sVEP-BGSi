import hashlib
import os

from shared.utils import fetch_remote_content, query_references_table

REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]

ENSEMBL_VERSION_URL = "https://ftp.ensembl.org/pub/VERSION"
MIRNA_GFF_URL = "https://www.mirbase.org/download/hsa.gff3"


def check_ensembl_version():
    id = "ensembl_version"
    local_ensembl_version = query_references_table(id)
    remote_ensembl_version = (
        fetch_remote_content(ENSEMBL_VERSION_URL).decode("utf-8").strip()
    )
    return remote_ensembl_version != local_ensembl_version, remote_ensembl_version


def check_mirna_hash():
    id = "mirna_hash"
    mirna_content = fetch_remote_content(MIRNA_GFF_URL)
    local_mirna_hash = query_references_table(id)
    remote_mirna_hash = hashlib.md5(mirna_content).hexdigest()
    return [remote_mirna_hash != local_mirna_hash, remote_mirna_hash]
