import hashlib
import os
import xml.etree.ElementTree as ET

from shared.utils import fetch_remote_content, query_references_table
from clinvar import CLINVAR_FTP_PATH, CLINVAR_FTP_FILE

REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]

ENSEMBL_VERSION_URL = "https://ftp.ensembl.org/pub/VERSION"
GNOMAD_CONSTRAINTS_VERSION = os.environ["GNOMAD_CONSTRAINTS_VERSION"]
MIRNA_GFF_URL = "https://www.mirbase.org/download/hsa.gff3"


def check_clinvar_version():
    id = "clinvar_version"
    clinvar_index_html = fetch_remote_content(CLINVAR_FTP_PATH)
    root = ET.fromstring(clinvar_index_html)
    latest_row = [
        row for row in root.findall(".//tr")
        if (
            (anchor := row.find(".//a")) is not None
            and anchor.attrib.get("href") == CLINVAR_FTP_FILE
        )
    ][0]
    latest_version = latest_row.findall("td")[3].text.split(' ')[0]
    local_clinvar_version = query_references_table(id)
    return [latest_version != local_clinvar_version, latest_version]


def check_ensembl_version():
    id = "ensembl_version"
    local_ensembl_version = query_references_table(id)
    remote_ensembl_version = (
        fetch_remote_content(ENSEMBL_VERSION_URL).decode("utf-8").strip()
    )
    return remote_ensembl_version != local_ensembl_version, remote_ensembl_version


def check_gnomad_constraints_version():
    id = "gnomad_constraints_version"
    local_gnomad_version = query_references_table(id)
    return (
        GNOMAD_CONSTRAINTS_VERSION != local_gnomad_version,
        GNOMAD_CONSTRAINTS_VERSION,
    )


def check_mirna_hash():
    id = "mirna_hash"
    mirna_content = fetch_remote_content(MIRNA_GFF_URL)
    local_mirna_hash = query_references_table(id)
    remote_mirna_hash = hashlib.md5(mirna_content).hexdigest()
    return [remote_mirna_hash != local_mirna_hash, remote_mirna_hash]
