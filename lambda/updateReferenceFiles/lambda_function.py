from clinvar import update_clinvar
from ensembl import process_ensembl_gtf, process_ensembl_fasta, update_ensembl
from constraints import process_constraints, update_constraints
from mirna import process_mirna_gff, update_mirna
from shared.utils import get_sns_event
from version_checks import (
    check_clinvar_version,
    check_ensembl_version,
    check_gnomad_constraints_version,
    check_mirna_hash,
)


def lambda_handler(event, _):
    if event.get("source") == "aws.events":
        clinvar_outdated, clinvar_version = check_clinvar_version()
        ensembl_outdated, ensembl_version = check_ensembl_version()
        gnomad_constraints_outdated, gnomad_constraints_version = (
            check_gnomad_constraints_version()
        )
        mirna_outdated, mirna_hash = check_mirna_hash()

        if clinvar_outdated:
            update_clinvar(clinvar_version)

        if ensembl_outdated:
            update_ensembl(ensembl_version)

        if gnomad_constraints_outdated:
            update_constraints(gnomad_constraints_version)

        if mirna_outdated:
            update_mirna(mirna_hash)

    elif "Records" in event and event["Records"][0].get("EventSource") == "aws:sns":
        message = get_sns_event(event)
        match message["file_type"]:
            case "ensembl_gtf":
                process_ensembl_gtf(message["file_url"])
            case "ensembl_fasta":
                process_ensembl_fasta(message["file_url"], message["chr"])
            case "gnomad_constraints":
                process_constraints(message["gnomad_version"])
            case "mirna_gff":
                process_mirna_gff(message["file_url"])
