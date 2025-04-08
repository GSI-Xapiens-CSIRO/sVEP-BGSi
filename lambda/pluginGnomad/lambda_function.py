import json
import os

from shared.utils import (
    Orchestrator,
    s3,
    handle_failed_execution,
    decompress_sns_data,
)


GNOMAD_PUBLIC_CHR1 = os.environ["GNOMAD_PUBLIC_CHR1"]
SVEP_REGIONS = os.environ["SVEP_REGIONS"]


def lambda_handler(event, _):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]
    chrom_mapping = message["mapping"]
    request_id = message["requestId"]

    print("SNS data: ", decompress_sns_data(sns_data))
    print("Chrom mapping: ", chrom_mapping)

    try:
        rows = [row.split("\t") for row in sns_data.split("\n") if row]

        # new_rows = add_clinvar_columns(rows, chrom_mapping)

        # base_filename = orchestrator.temp_file_name
        # sns_data = "\n".join("\t".join(row) for row in new_rows)

        # # TODO Delete upload result function to SVEP_REGIONS (Latest plugin will upload the result)
        # filename = f"/tmp/{base_filename}.tsv"
        # with open(filename, "w") as tsv_file:
        #     tsv_file.write(sns_data)
        # s3.Bucket(SVEP_REGIONS).upload_file(filename, f"{base_filename}.tsv")
        # orchestrator.mark_completed()
    except Exception as e:
        handle_failed_execution(request_id, e)
