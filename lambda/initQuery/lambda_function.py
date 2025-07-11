import json
from pathlib import Path
import os
import subprocess
import boto3

from botocore.client import ClientError

from shared.apiutils import bad_request, bundle_response
from shared.utils import (
    chrom_matching,
    print_event,
    orchestration,
    query_references_table,
)
from urllib.parse import urlparse

from shared.apiutils import bad_request, bundle_response
from shared.dynamodb import (
    check_user_in_project,
    update_clinic_job,
)
from dynamodb import does_clinic_job_exist_by_name

lambda_client = boto3.client("lambda")

# Environment variables
CONCAT_STARTER_SNS_TOPIC_ARN = os.environ["CONCAT_STARTER_SNS_TOPIC_ARN"]
RESULT_DURATION = int(os.environ["RESULT_DURATION"])
RESULT_SUFFIX = os.environ["RESULT_SUFFIX"]
SLICE_SIZE_MBP = int(os.environ["SLICE_SIZE_MBP"])
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

REGIONS = chrom_matching.get_regions(SLICE_SIZE_MBP)
REFERENCE_IDS = ["clinvar_version", "ensembl_version", "gnomad_constraints_version"]


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

        job_name_already_exists = does_clinic_job_exist_by_name(
            job_name.lower(), project
        )

        if job_name_already_exists:
            return bundle_response(
                200,
                {
                    "Success": False,
                    "Response": "Job name already exist",
                    "RequestId": request_id,
                    "ProjectName": project,
                },
            )

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

    reference_versions = {}
    try:
        for reference_id in REFERENCE_IDS:
            reference_versions[reference_id] = query_references_table(reference_id)
    except ClientError as e:
        return bad_request(
            "Unable to retrieve reference versions. Please contact an AWS administrator."
        )

    if any(version is None for version in reference_versions.values()):
        return bad_request(
            "Some reference versions are missing. Please contact an AWS administrator."
        )

    parsed_location = urlparse(location)
    input_vcf = Path(parsed_location.path.lstrip("/")).name
    update_clinic_job(
        job_id=request_id,
        job_name=job_name,
        job_status="pending",
        project_name=project,
        input_vcf=input_vcf,
        user_id=sub,
        reference_versions=reference_versions,
        skip_email=True,
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
            "Success": True,
        },
    )
