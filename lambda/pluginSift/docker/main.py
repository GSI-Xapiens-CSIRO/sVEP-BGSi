import os
# import json
# import subprocess
# import zipfile

# from shared.utils import Orchestrator, s3, download_sift_database


# Environment variables
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
SIFT_DATABASE_REFERENCE = os.environ["SIFT_DATABASE_REFERENCE"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

# [TODO] : Download siftdb
# download_sift_database(BUCKET_NAME, SIFT_DATABASE_REFERENCE)


# def run_sift_anotator(input, db, output):
#     try:
#         result = subprocess.run(
#             [
#                 "java",
#                 "-jar",
#                 "SIFT4G_Annotator.jar",
#                 "-c",
#                 "-i",
#                 input,
#                 "-d",
#                 db,
#                 "-r",
#                 output,
#                 "-t",
#             ],  # Run the JAR file
#             capture_output=True,
#             text=True,
#             check=True,
#         )
#         return {"statusCode": 200, "body": result.stdout}
#     except subprocess.CalledProcessError as e:
#         return {"statusCode": 500, "body": f"Error: {e.stderr}"}


# def parse_sift_output(output_file):
#     annotations = []
#     with open(output_file, "r") as file:
#         for line in file:
#             if line.startswith("#"):  # Skip headers
#                 continue
#             parts = line.strip().split("\t")
#             if len(parts) < 5:
#                 continue  # Skip invalid lines

#             # Extract relevant SIFT annotations
#             chrom, pos, ref, alt, sift_score = (
#                 parts[0],
#                 parts[1],
#                 parts[3],
#                 parts[4],
#                 parts[-1],
#             )

#             annotations.append(
#                 {
#                     "chrom": chrom,
#                     "pos": pos,
#                     "ref": ref,
#                     "alt": alt,
#                     "sift_score": sift_score,
#                 }
#             )
#     return annotations


# def merge_sift_annotations(original_data, sift_annotations):
#     updated_data = []
#     for row in original_data:
#         chrom, pos, ref, alt = row[0], row[1], row[3], row[4]

#         # Find matching SIFT annotation
#         sift_match = next(
#             (s for s in sift_annotations if s["chrom"] == chrom and s["pos"] == pos),
#             None,
#         )

#         if sift_match:
#             row.append(sift_match["sift_score"])  # Add new column
#         else:
#             row.append("NA")  # No match

#         updated_data.append(row)
#     return updated_data


def main(payload, _):
    print(f"Received message: {payload}")
    # event = json.loads(payload)
    # sns = event['Records'][0]['Sns']
    # message = json.loads(sns['Message'])
    # data = message['snsData']
    # request_id = message['requestId']

    # print(f"Data: {data}")
    # print(f"Request ID: {request_id}")
    # print("Processing SIFT data...")
    # return {"statusCode": 200, "body": "Success"}

    # orchestrator = Orchestrator(event)
    # message = orchestrator.message
    # sns_data = message["snsData"]

    # # Save original SNS data to a temporary VCF file
    # sns_data_filename = f"/tmp/{orchestrator.temp_file_name}_sns_data.vcf"
    # with open(sns_data_filename, "w") as sns_file:
    #     sns_file.write(sns_data)

    # # Unzip the SIFT database
    # sift_db_zip_path = f"/tmp/{SIFT_DATABASE_REFERENCE}"
    # sift_db_extract_path = f"/tmp/{SIFT_DATABASE_REFERENCE}/DB"
    # with zipfile.ZipFile(sift_db_zip_path, 'r') as zip_ref:
    #     zip_ref.extractall(sift_db_extract_path)

    # # Run the SIFT annotator
    # result = run_sift_anotator(
    #     sns_data_filename,
    #     f"/tmp/{SIFT_DATABASE_REFERENCE}/DB",
    #     orchestrator.temp_file_name,
    # )

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
