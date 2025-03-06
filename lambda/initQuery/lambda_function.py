import json
from pathlib import Path
import os
import subprocess
import boto3

from shared.apiutils import bad_request, bundle_response
from shared.utils import (
    chrom_matching,
    print_event,
    sns_publish,
    start_function,
    ENV_COGNITO,
)
from dynamodb import check_user_in_project
from urllib.parse import urlparse

from shared.apiutils import bad_request, bundle_response
from shared.utils import chrom_matching, print_event, sns_publish, start_function
from shared.dynamodb import check_user_in_project, update_clinic_job

lambda_client = boto3.client("lambda")

# Environment variables
CONCAT_STARTER_SNS_TOPIC_ARN = os.environ["CONCAT_STARTER_SNS_TOPIC_ARN"]
QUERY_VCF_SNS_TOPIC_ARN = os.environ["QUERY_VCF_SNS_TOPIC_ARN"]
RESULT_DURATION = int(os.environ["RESULT_DURATION"])
RESULT_SUFFIX = os.environ["RESULT_SUFFIX"]
SLICE_SIZE_MBP = int(os.environ["SLICE_SIZE_MBP"])
COGNITO_SVEP_SUCCESS_EMAIL_LAMBDA = ENV_COGNITO.COGNITO_SVEP_SUCCESS_EMAIL_LAMBDA
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

REGIONS = chrom_matching.get_regions(SLICE_SIZE_MBP)


def get_translated_regions_and_mapping(location):
    vcf_chromosomes = chrom_matching.get_vcf_chromosomes(location)
    vcf_regions = []
    for target_chromosome, region_list in REGIONS.items():
        chromosome = chrom_matching.get_matching_chromosome(
            vcf_chromosomes, target_chromosome
        )
        if not chromosome:
            continue
        vcf_regions += [f"{chromosome}:{region}" for region in region_list]
    chrom_mapping = chrom_matching.get_chromosome_mapping(vcf_chromosomes)
    return vcf_regions, chrom_mapping


def get_sample_count(location):
    cmd = f'bcftools query -l "{location}" | wc -l'
    result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    return int(result.stdout.strip())


def lambda_handler(event, _):
    print_event(event, max_length=None)
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    event_body = event.get("body")

    if not event_body:
        return bad_request("No body sent with request.")
    try:
        body_dict = json.loads(event_body)
        request_id = event["requestContext"]["requestId"]
        project = body_dict["projectName"]
        location = body_dict["location"]
        check_user_in_project(sub, project)
    except ValueError:
        return bad_request("Error parsing request body, Expected JSON.")
    try:
        vcf_regions, chrom_mapping = get_translated_regions_and_mapping(location)
    except chrom_matching.ChromosomeNotFoundError as e:
        return bad_request(str(e))
    except Exception:
        return bad_request(
            "An error occurred, please check your input and try again later."
        )

    try:
        sample_count = get_sample_count(location)
    except subprocess.CalledProcessError as e:
        return bad_request(str(e))

    if sample_count != 1:
        return bad_request("Only single-sample VCFs are supported.")

    print(vcf_regions)
    start_function(
        QUERY_VCF_SNS_TOPIC_ARN,
        request_id,
        {
            "requestId": request_id,
            "regions": vcf_regions,
            "location": location,
            "mapping": chrom_mapping,
        },
    )
    sns_publish(
        CONCAT_STARTER_SNS_TOPIC_ARN,
        {
            "requestId": request_id,
            "project": project,
        },
    )

    # payload = {
    #     "body": {
    #         "email": "fajarsep12@gmail.com",
    #         "first_name": "Fajar",
    #         "last_name": "Septiawan",
    #         "file": "file.vcf",
    #         "project_name": "project test",
    #     }
    # }

    # response = lambda_client.invoke(
    #     FunctionName=COGNITO_SVEP_SUCCESS_EMAIL_LAMBDA,
    #     InvocationType="RequestResponse",
    #     Payload=json.dumps(payload),
    # )
    # if not (payload_stream := response.get("Payload")):
    #     raise Exception("Error invoking email Lambda: No response payload")
    # body = json.loads(payload_stream.read().decode("utf-8"))
    # if not body.get("success", False):
    #     raise Exception(f"Error invoking email Lambda: {body.get('message')}")
    # email_sent = body.get("success", False)

    parsed_location = urlparse(location)
    input_vcf = Path(parsed_location.path.lstrip("/")).name
    update_clinic_job(
        job_id=request_id,
        job_status="pending",
        project_name=project,
        input_vcf=input_vcf,
        user_id=sub,
    )

    return bundle_response(
        200,
        {
            "Response": "Process started",
            "RequestId": request_id,
            "ProjectName": project,
        },
    )
