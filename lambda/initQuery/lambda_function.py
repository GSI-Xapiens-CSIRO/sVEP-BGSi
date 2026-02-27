import json
from pathlib import Path
import os
import subprocess
import traceback

import boto3
from botocore.client import ClientError
import requests
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
from functools import lru_cache

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
from shared.utils import (
    require_permission,
    require_any_permission,
    InsufficientPermissionError,
)

# Environment variables
CONCAT_STARTER_SNS_TOPIC_ARN = os.environ["CONCAT_STARTER_SNS_TOPIC_ARN"]
SLICE_SIZE_MBP = int(os.environ["SLICE_SIZE_MBP"])
ALLOWED_SNS_TOPIC_ARNS = os.environ.get("ALLOWED_SNS_TOPIC_ARNS", "").split(",")
os.environ["PATH"] += f":{os.environ['LAMBDA_TASK_ROOT']}"

REGIONS = chrom_matching.get_regions(SLICE_SIZE_MBP)
REFERENCE_IDS = ["clinvar_version", "ensembl_version", "gnomad_constraints_version"]


@lru_cache(maxsize=10)
def get_sns_certificate(cert_url: str):
    """Fetch and cache SNS signing certificate."""
    # Validate cert URL is from AWS
    if not cert_url.startswith("https://sns.") or ".amazonaws.com/" not in cert_url:
        raise ValueError("Invalid certificate URL - not from AWS SNS")
    
    response = requests.get(cert_url, timeout=5)
    response.raise_for_status()
    return load_pem_x509_certificate(response.content)


def verify_sns_signature(record: dict) -> bool:
    """
    Verify that an SNS message is genuinely from AWS SNS.
    Returns True if valid, raises exception otherwise.
    """
    sns_message = record.get("Sns", {})
    
    # Build the string to sign based on message type
    message_type = sns_message.get("Type", "Notification")
    
    if message_type == "Notification":
        fields = ["Message", "MessageId", "Subject", "Timestamp", "TopicArn", "Type"]
    else:
        # SubscriptionConfirmation or UnsubscribeConfirmation
        fields = ["Message", "MessageId", "SubscribeURL", "Timestamp", "Token", "TopicArn", "Type"]
    
    string_to_sign = ""
    for field in fields:
        value = sns_message.get(field)
        if value is not None:
            string_to_sign += f"{field}\n{value}\n"
    
    # Get certificate and verify signature
    cert_url = sns_message.get("SigningCertUrl") or sns_message.get("SigningCertURL")
    if not cert_url:
        raise ValueError("Missing SigningCertUrl in SNS message")
    
    certificate = get_sns_certificate(cert_url)
    signature = base64.b64decode(sns_message.get("Signature", ""))
    
    # Verify signature
    public_key = certificate.public_key()
    public_key.verify(
        signature,
        string_to_sign.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA1(),  # SNS uses SHA1 for signatures
    )
    
    return True


def validate_sns_source(record: dict):
    """Validate that SNS message is from a trusted topic."""
    topic_arn = record.get("Sns", {}).get("TopicArn", "")
    
    if ALLOWED_SNS_TOPIC_ARNS and ALLOWED_SNS_TOPIC_ARNS[0]:  # Check if configured
        if topic_arn not in ALLOWED_SNS_TOPIC_ARNS:
            raise ValueError(f"SNS message from unauthorized topic: {topic_arn}")
    
    return True


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
        record = event["Records"][0]
        
        # 🔐 Verify SNS signature to ensure message is from AWS
        try:
            verify_sns_signature(record)
        except Exception as e:
            return {
                "Success": False,
                "error": f"SNS signature verification failed: {str(e)}",
            }
        
        # 🔐 Validate the message is from an allowed topic
        try:
            validate_sns_source(record)
        except ValueError as e:
            return {
                "Success": False,
                "error": str(e),
            }
        
        message = json.loads(record["Sns"]["Message"])
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
        result["success"] = True
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
        "sub": event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims")
        .get("sub"),
    }
    if not result["sub"]:
        result["error"] = "User not authenticated."
        return result

    required_fields = ["projectName", "location", "jobName"]
    try:
        for field in required_fields:
            result[field] = body[field]
        result["success"] = True
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
    location = result["location"]

    try:
        check_user_in_project(sub, project)
    except Exception as e:
        result["error"] = f"Error checking user in project: {str(e)}"
        return handle_init_failure(result, is_batch_job)

    # 🔐 Only enforce permission for API Gateway calls
    if not is_batch_job:
        try:
            require_any_permission(
                event,
                [
                    "clinical_workflow_execution.create",
                    "clinical_workflow_execution.update",
                ],
            )
        except InsufficientPermissionError as e:
            return bundle_response(
                403,
                {
                    "Success": False,
                    "Message": str(e),
                },
            )

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
