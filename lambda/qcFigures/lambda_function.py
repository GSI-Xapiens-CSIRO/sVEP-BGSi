import subprocess
import os
import boto3
from uuid import uuid4
from shared.apiutils import bad_request, bundle_response
from shared.utils import get_sns_event, download_to_tmp


s3_client = boto3.client("s3")

BUCKET_NAME = os.environ["FILE_LOCATION"]


def lambda_handler(event, context):
    message = get_sns_event(event)
    project_name = message["project"]
    file_name = message["file_name"]
    
    input_vcf_file = f"/projects/{project_name}/project-files/{file_name}"
    
    try:
        download_to_tmp(BUCKET_NAME,input_vcf_file,raise_on_notfound=True)
        # TODO add function for running vcfstats
        # TODO upload vcfstats result to BUCKET_NAME
        output_vcfstats_file = f"{BUCKET_NAME}/projects/{project_name}/qc-figures/{file_name}"
        s3_url = "get url"
        # TODO delete VCF file on /tmp
        return bundle_response(
            200,
            {
                "message": "Image generated and uploaded successfully",
                "image_url": s3_url,
            },
        )

    except subprocess.CalledProcessError as e:
        # TODO delete VCF file on /tmp/{input_vcf_file}
        return bundle_response(
            500,
            {
                "body": {"message": f"Error running vcfstats: {str(e)}"},
            },
        )
    except Exception as e:
        # TODO delete VCF file on /tmp
        return bundle_response(
            500,
            {
                "body": {"message": f"Error generating image: {str(e)}"},
            },
        )
