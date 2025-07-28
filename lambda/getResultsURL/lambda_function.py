import os
import json
import gzip

import boto3
import botocore

from shared.apiutils import bad_request, bundle_response
from shared.utils import (
    print_event,
    generate_presigned_get_url,
)
from shared.indexutils import search_index_entry, get_index_page
from dynamodb import check_user_in_project

# Environment variables
RESULT_BUCKET = os.environ["SVEP_RESULTS"]
RESULT_DURATION = int(os.environ["RESULT_DURATION"])
RESULT_SUFFIX = os.environ["RESULT_SUFFIX"]

# Load FILTERS from environment variable
FILTERS = json.loads(os.environ.get("FILTERS", "{}"))

s3_resource = boto3.resource("s3")
s3_client = boto3.client("s3")


def read_from_s3(bucket_name, key, at, size):
    byte_range = f"bytes={at}-{at + size - 1}"
    response = s3_client.get_object(Bucket=bucket_name, Key=key, Range=byte_range)
    return response["Body"].read()


def read_size_from_s3(bucket_name, key):
    response = s3_client.head_object(Bucket=bucket_name, Key=key)
    return response["ContentLength"]


def get_index(key):
    try:
        index = s3_resource.Object(RESULT_BUCKET, key).get()
        index = gzip.decompress(index["Body"].read())
        index = json.loads(index)
        return index
    except botocore.exceptions.ClientError:
        return None


def lambda_handler(event, _):
    print_event(event, max_length=None)

    try:
        sub = event["requestContext"]["authorizer"]["claims"]["sub"]
        request_id = event["queryStringParameters"]["request_id"]
        project_name = event["queryStringParameters"]["project_name"]
        results_path = (
            f"projects/{project_name}/clinical-workflows/{request_id}{RESULT_SUFFIX}"
        )
        index_path = f"{results_path}.index.json.gz"

        check_user_in_project(sub, project_name)

        if 0 < read_size_from_s3(RESULT_BUCKET, results_path) < 5 * 10**6:
            content = read_from_s3(
                RESULT_BUCKET,
                results_path,
                0,
                read_size_from_s3(RESULT_BUCKET, results_path),
            )
            return bundle_response(
                200,
                {
                    "url": None,
                    "chromosome": "-",
                    "pages": {"-": 1},
                    "page": 1,
                    "content": content.decode("utf-8"),
                    "filters": FILTERS,
                },
            )

        if index := get_index(index_path):
            chromosomes = list(index.keys())
            page = event["queryStringParameters"].get("page", 1)
            position = event["queryStringParameters"].get("position", None)
            chromosome = event["queryStringParameters"].get(
                "chromosome", chromosomes[0]
            )

            if chromosome not in chromosomes:
                return bad_request("Invalid chromosome.")

            if position:
                entry = search_index_entry(index, chromosome, int(position))
            else:
                entry = get_index_page(index, chromosome, int(page))

            content = read_from_s3(
                RESULT_BUCKET,
                results_path,
                entry["page_start_f"],
                entry["page_end_f"] - entry["page_start_f"],
            )

            return bundle_response(
                200,
                {
                    "url": None,
                    "chromosome": chromosome,
                    "pages": {
                        chrom: len(index[chrom]["page_start_f"])
                        for chrom in index.keys()
                    },
                    "page": entry["page"],
                    "content": content.decode("utf-8"),
                    "filters": FILTERS,
                },
            )
        else:
            result_url = generate_presigned_get_url(
                RESULT_BUCKET,
                results_path,
                RESULT_DURATION,
            )
            return bundle_response(
                200,
                {
                    "url": result_url,
                    "pages": [],
                    "page": 1,
                    "content": None,
                    "chromosome": None,
                    "filters": FILTERS,
                },
            )
    except ValueError:
        return bad_request("Error parsing request body, Expected JSON.")
    except KeyError:
        return bad_request("Invalid parameters.")
    except Exception as e:
        print("Unhandled", e)
        return bad_request("Unhandled exception. Please contact admin with the jobId.")
