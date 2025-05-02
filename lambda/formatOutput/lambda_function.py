import os

from shared.utils import orchestration, s3


# Environment variables
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
COLUMNS = os.environ["COLUMNS"].split(",")
OUTPUT_NAME = "output.tsv"
NULL_VALUE = "-"


def format_output(sns_data, upload_filename):
    filename = f"/tmp/{OUTPUT_NAME}"
    print(f"Formatting {len(sns_data)} rows as TSV")
    with open(filename, "w") as tsv_file:
        print(
            "\n".join(
                "\t".join(str(row.get(column, NULL_VALUE)) for column in COLUMNS)
                for row in sns_data
            ),
            file=tsv_file,
        )
    print(f"Uploading file to s3://{SVEP_REGIONS}/{upload_filename}")
    s3.Bucket(SVEP_REGIONS).upload_file(filename, upload_filename)


def lambda_handler(event, _):
    with orchestration(event) as orc:
        sns_data = orc.message["snsData"]
        format_output(sns_data, f"{orc.temp_file_name}.tsv")
