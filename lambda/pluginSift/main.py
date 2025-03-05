import os
import subprocess

from shared.utils import Orchestrator, s3, download_bedfile, start_function


# Environment variables
SVEP_REGIONS = os.environ["SVEP_REGIONS"]
BUCKET_NAME = os.environ["REFERENCE_LOCATION"]
SIFT_DATABASE_REFERENCE = os.environ["SIFT_DATABASE_REFERENCE"]
PLUGIN_SIFT_SNS_TOPIC_ARN = os.environ["PLUGIN_SIFT_SNS_TOPIC_ARN"]
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

# [TODO] : Download siftdb
download_siftdb(BUCKET_NAME, SIFT_DATABASE_REFERENCE)

def run_sift_anotator(input, db, output):
    try:
        result = subprocess.run(
            ["java", "-jar", "SIFT4G_Annotator.jar", "-c", "-i", input, "-d", db, "-r", output, "-t"],  # Run the JAR file
            capture_output=True, 
            text=True, 
            check=True
        )
        return {
            "statusCode": 200,
            "body": result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {
            "statusCode": 500,
            "body": f"Error: {e.stderr}"
        }


def main(event, _):
    orchestrator = Orchestrator(event)
    message = orchestrator.message
    sns_data = message["snsData"]

    # Create a file with the content of sns_data
    sns_data_filename = f"/tmp/{orchestrator.temp_file_name}_sns_data.vcf"
    with open(sns_data_filename, "w") as sns_file:
        sns_file.write(sns_data)

    # Run the SIFT annotator
    result = run_sift_anotator(sns_data_filename, f"/tmp/{SIFT_DATABASE_REFERENCE}", orchestrator.temp_file_name)

    base_filename = orchestrator.temp_file_name

    filename = f"/tmp/{base_filename}.tsv"
    with open(filename, "w") as tsv_file:
        tsv_file.write(sns_data)
    s3.Bucket(SVEP_REGIONS).upload_file(filename, f"{base_filename}.tsv")
    orchestrator.mark_completed()
