from ensembl import process_ensembl_gtf, process_ensembl_fasta, update_ensembl
from mirna import process_mirna_gff, update_mirna
from shared.utils import get_sns_event
from version_checks import check_ensembl_version, check_mirna_hash


def lambda_handler(event, _):
    if event.get("source") == "aws.events":
        ensembl_outdated, ensembl_version = check_ensembl_version()
        mirna_outdated, mirna_hash = check_mirna_hash()

        if ensembl_outdated:
            update_ensembl(ensembl_version)

        if mirna_outdated:
            update_mirna(mirna_hash)

    elif "Records" in event and event["Records"][0].get("EventSource") == "aws:sns":
        message = get_sns_event(event)
        match message["file_type"]:
            case "ensembl_gtf":
                process_ensembl_gtf(message["file_url"])
            case "ensembl_fasta":
                process_ensembl_fasta(message["file_url"], message["chr"])
            case "mirna_gff":
                process_mirna_gff(message["file_url"])
