import json
import os
import gzip
import base64
import hail as hl

# GNOMAD_GENOMES_PATH = os.environ["GNOMAD_GENOMES_PATH"]
# SVEP_REGIONS = os.environ["SVEP_REGIONS"]


hl.init()


def decompress_sns_data(encoded_data: str) -> str:
    compressed = base64.b64decode(encoded_data)  # Decode from Base64
    return gzip.decompress(compressed).decode("utf-8")  # Decompress with gzip


def lambda_handler(event, _):
    message = json.loads(event["Records"][0]["Sns"]["Message"])

    sns_data = message["snsData"]
    chrom_mapping = message["mapping"]
    request_id = message["requestId"]

    print("SNS data: ", sns_data)
    print("Chrom mapping: ", chrom_mapping)

    rows = [row.split("\t") for row in sns_data.split("\n") if row]
