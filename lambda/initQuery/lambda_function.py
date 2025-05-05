import json
from pathlib import Path
import os
import subprocess
import boto3

from shared.apiutils import bad_request, bundle_response
from shared.utils import (
    chrom_matching,
    print_event,
    orchestration,
)
from dynamodb import check_user_in_project
from urllib.parse import urlparse

from shared.apiutils import bad_request, bundle_response
from shared.dynamodb import check_user_in_project, update_clinic_job

lambda_client = boto3.client("lambda")

# Environment variables
CONCAT_STARTER_SNS_TOPIC_ARN = os.environ["CONCAT_STARTER_SNS_TOPIC_ARN"]
RESULT_DURATION = int(os.environ["RESULT_DURATION"])
RESULT_SUFFIX = os.environ["RESULT_SUFFIX"]
SLICE_SIZE_MBP = int(os.environ["SLICE_SIZE_MBP"])
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
    result = subprocess.run(
        ["bcftools", "query", "-l", location],
        check=True,
        capture_output=True,
        text=True,
    )
    return len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0


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
        job_name = body_dict["jobName"]

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

    parsed_location = urlparse(location)
    input_vcf = Path(parsed_location.path.lstrip("/")).name
    update_clinic_job(
        job_id=request_id,
        job_name=job_name,
        job_status="pending",
        project_name=project,
        input_vcf=input_vcf,
        user_id=sub,
    )
    print(vcf_regions)
    with orchestration(request_id=request_id) as orc:
        orc.next_function(
            message={
                "regions": vcf_regions,
                "location": location,
                "mapping": chrom_mapping,
            },
        )
        orc.start_function(
            CONCAT_STARTER_SNS_TOPIC_ARN,
            {
                "project": project,
            },
        )
    return bundle_response(
        200,
        {
            "Response": "Process started",
            "RequestId": request_id,
            "ProjectName": project,
        },
    )
