import json
from pathlib import Path
import os
import subprocess
import traceback

import boto3
from botocore.client import ClientError

from shared.apiutils import bad_request, bundle_response
from shared.utils import (
    chrom_matching,
    handle_failed_execution,
    print_event,
    orchestration,
    query_references_table,
)
from urllib.parse import urlparse

from shared.dynamodb import (
    check_user_in_project,
    update_clinic_job,
)
from dynamodb import does_clinic_job_exist_by_name

# Environment variables
CONCAT_STARTER_SNS_TOPIC_ARN = os.environ["CONCAT_STARTER_SNS_TOPIC_ARN"]
SLICE_SIZE_MBP = int(os.environ["SLICE_SIZE_MBP"])
os.environ["PATH"] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

REGIONS = chrom_matching.get_regions(SLICE_SIZE_MBP)
REFERENCE_IDS = ["clinvar_version", "ensembl_version", "gnomad_constraints_version"]


def handle_init_failure(result, is_batch_job):
    """
    Handles failure responses for both batch and non-batch jobs.
    Batch jobs will log the error and update the job status in DynamoDB.
    Non-batch jobs will return a bad request response.
    """
    error_message = result.get("error", "Unknown error")
    if is_batch_job:
        if request_id := result.get("requestId"):
            handle_failed_execution(request_id, error_message)
        else:
            print(
                "Error in batch job without requestId:",
                error_message,
            )
    else:
        return bad_request(error_message)


def parse_sns(event):
    try:
        message = json.loads(event["Records"][0]["Sns"]["Message"])
    except (KeyError, ValueError) as e:
        return {
            "success": False,
            "error": f"Error parsing SNS message: {str(e)}",
        }

    result = {
        "success": False,
        "requestId": message.get("requestId"),
    }

    required_fields = ["sub", "projectName", "location", "jobName"]
    try:
        for field in required_fields:
            result[field] = message[field]
    except KeyError as e:
        result["error"] = f"Missing expected field in SNS message: {str(e)}"

    return result


def parse_api_gateway(event):
    try:
        body = json.loads(event["body"])
    except ValueError:
        return {
            "success": False,
            "error": "Error parsing request body: Invalid JSON.",
        }

    result = {
        "success": False,
        "requestId": event.get("requestContext", {}).get("requestId"),
        "sub": event.get("requestContext", {}).get("authorizer", {}).get("sub"),
    }
    if not result["sub"]:
        result["error"] = "User not authenticated."
        return result

    required_fields = ["sub", "projectName", "location", "jobName"]
    try:
        for field in required_fields:
            result[field] = body[field]
    except KeyError as e:
        result["error"] = f"Missing expected field in request body: {str(e)}"

    return result


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
    is_batch_job = False
    if "Records" in event and event["Records"][0].get("EventSource") == "aws:sns":
        is_batch_job = True

    result = parse_sns(event) if is_batch_job else parse_api_gateway(event)
    if not result.get("success", False):
        return handle_init_failure(result, is_batch_job)

    request_id = result["requestId"]
    sub = result["sub"]
    project = result["projectName"]
    job_name = result["jobName"]
    location = result.get("location")

    try:
        check_user_in_project(sub, project)
    except Exception as e:
        result["error"] = f"Error checking user in project: {str(e)}"
        return handle_init_failure(result, is_batch_job)

    job_name_exists = (not is_batch_job) and does_clinic_job_exist_by_name(
        job_name.lower(), project
    )
    if job_name_exists:
        result["error"] = (
            f"Job name '{job_name}' already exists in project '{project}'."
        )
        return handle_init_failure(result, is_batch_job)

    try:
        vcf_regions, chrom_mapping = get_translated_regions_and_mapping(location)
    except chrom_matching.ChromosomeNotFoundError as e:
        result["error"] = f"Chromosome not found in VCF: {str(e)}"
        return handle_init_failure(result, is_batch_job)
    except Exception as e:
        result["error"] = f"Error processing VCF: {str(e)}"
        return handle_init_failure(result, is_batch_job)

    try:
        sample_count = get_sample_count(location)
    except subprocess.CalledProcessError as e:
        result["error"] = f"Error counting samples: {str(e)}"
        return handle_init_failure(result, is_batch_job)

    if sample_count != 1:
        result["error"] = "Only single-sample VCFs are supported"
        return handle_init_failure(result, is_batch_job)

    reference_versions = {}
    failed_ids = []
    for reference_id in REFERENCE_IDS:
        try:
            version = query_references_table(reference_id)
            reference_versions[reference_id] = version
        except ClientError as e:
            traceback.print_exc()
            failed_ids.append(reference_id)
    if failed_ids:
        result["error"] = (
            f"Unable to retrieve reference versions for: {', '.join(failed_ids)}. "
            "Please contact an AWS administrator."
        )
        return handle_init_failure(result, is_batch_job)
    missing_references = [
        ref_id for ref_id, version in reference_versions.items() if version is None
    ]
    if missing_references:
        result["error"] = (
            f"Missing reference versions for: {', '.join(missing_references)}. "
            "Please contact an AWS administrator."
        )
        return handle_init_failure(result, is_batch_job)

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
