import os
import json
import subprocess
import zipfile
import boto3
import botocore
import io

# Environment variables
SVEP_TEMP = os.environ.get("SVEP_TEMP")
REGION = os.environ.get("REGION")
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
SIFT_DATABASE_REFERENCE = os.environ["SIFT_DATABASE_REFERENCE"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'


def download_and_unzip_from_s3(bucket, key, extract_to):
    s3 = boto3.client('s3')
    try:
        # Create an in-memory bytes buffer
        buffer = io.BytesIO()
        
        # Download the file from S3 into the buffer
        s3.download_fileobj(bucket, key, buffer)
        
        # Seek to the beginning of the buffer
        buffer.seek(0)
        
        # Unzip the file from the buffer
        with zipfile.ZipFile(buffer, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        return True
    except botocore.exceptions.ClientError as error:
        print(f"Error downloading file from S3: {error}")
        if error.response['Error']['Code'] == '404':
            return False
        else:
            raise error

def run_sift_anotator(input, db, output):
    try:
        result = subprocess.run(
            [
                "java",
                "-jar",
                "SIFT4G_Annotator.jar",
                "-c",
                "-i",
                input,
                "-d",
                db,
                "-r",
                output,
                "-t",
            ],  # Run the JAR file
            capture_output=True,
            text=True,
            check=True,
        )
        return {"statusCode": 200, "body": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"statusCode": 500, "body": f"Error: {e.stderr}"}


def parse_sift_output(output_file):
    annotations = []
    with open(output_file, "r") as file:
        for line in file:
            if line.startswith("#"):  # Skip headers
                continue
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue  # Skip invalid lines

            # Extract relevant SIFT annotations
            chrom, pos, ref, alt, sift_score = (
                parts[0],
                parts[1],
                parts[3],
                parts[4],
                parts[-1],
            )

            annotations.append(
                {
                    "chrom": chrom,
                    "pos": pos,
                    "ref": ref,
                    "alt": alt,
                    "sift_score": sift_score,
                }
            )
    return annotations


def merge_sift_annotations(original_data, sift_annotations):
    updated_data = []
    for row in original_data:
        chrom, pos, ref, alt = row[0], row[1], row[3], row[4]

        # Find matching SIFT annotation
        sift_match = next(
            (s for s in sift_annotations if s["chrom"] == chrom and s["pos"] == pos),
            None,
        )

        if sift_match:
            row.append(sift_match["sift_score"])  # Add new column
        else:
            row.append("NA")  # No match

        updated_data.append(row)
    return updated_data


def handler(event):
    try:
        print(f"Received message: {event}")
        sns = event['Records'][0]['Sns']
        message = json.loads(sns['Message'])  # Parse the JSON string in the 'Message' field
        data = message['snsData']
        request_id = message['requestId']
        temp_file_name = message['tempFileName']
        chrom_mapping = message['mapping']

        # print(f"Data: {data}")
        print(f"Request ID: {request_id}")
        print(f"Temp File Name: {temp_file_name}")
        print(f"Chrom Mapping: {chrom_mapping}")
        print("Processing SIFT data...")

        # Save original SNS data to a temporary VCF file
        sns_data_filename = f"/tmp/{temp_file_name}_sns_data.vcf"
        print(f"Saving SNS data to a temporary VCF file... {sns_data_filename}")
        with open(sns_data_filename, "w") as sns_file:
            sns_file.write(data)

        # Count total lines of sns_data_filename
        with open(sns_data_filename, "r") as file:
            total_lines = sum(1 for line in file)
        print(f"Total lines in SNS data file: {total_lines}")    

        print(f"Downloading and unzipping SIFT database... from {BUCKET_NAME}/{SIFT_DATABASE_REFERENCE}")
        sift_db_extract_path = f"/tmp/{SIFT_DATABASE_REFERENCE}/DB"
        download_and_unzip_from_s3(BUCKET_NAME, SIFT_DATABASE_REFERENCE, sift_db_extract_path)

        # List contents of /tmp directory
        print("Contents of /tmp directory before running SIFT annotator:\n" + "\n".join(os.listdir("/tmp")))

        # Run the SIFT annotator
        print(f"Running SIFT annotator... {sns_data_filename} /tmp/{SIFT_DATABASE_REFERENCE}/DB /tmp")
        result = run_sift_anotator(
            sns_data_filename,
            sift_db_extract_path,
            f"/tmp",
        )

        # List contents of /tmp directory
        print("Contents of /tmp directory after running SIFT annotator:\n" + "\n".join(os.listdir("/tmp")))

        # # Parse SIFT output from `stdout`
        # sift_annotations = parse_sift_output(result["body"])

        # # Merge original data with SIFT annotations
        # original_rows = [row.split("\t") for row in sns_data.split("\n") if row]
        # enriched_rows = merge_sift_annotations(original_rows, sift_annotations)

        # # Write enriched data to a TSV file
        # base_filename = orchestrator.temp_file_name
        # tsv_filename = f"/tmp/{base_filename}.tsv"

        # with open(tsv_filename, "w") as tsv_file:
        #     for row in enriched_rows:
        #         tsv_file.write("\t".join(row) + "\n")

        # s3.Bucket(SVEP_REGIONS).upload_file(tsv_filename, f"{base_filename}.tsv")
        # orchestrator.mark_completed()
        return {"statusCode": 200, "body": "Success"}
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": f"Error: {str(e)}"}