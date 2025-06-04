import os
import sys

import pytest
from moto import mock_aws
import boto3

from test_utils.mock_resources import setup_resources

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../lambda/formatOutput"))
)
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../shared_resources/python-modules/python",
        )
    )
)


@pytest.fixture(autouse=True, scope="session")
def resources_dict():
    with mock_aws():
        s3_client = boto3.client("s3")

        s3_client.create_bucket(
            Bucket=os.environ["SVEP_TEMP"],
            CreateBucketConfiguration={
                "LocationConstraint": os.environ["AWS_DEFAULT_REGION"],
            },
        )
        s3_client.create_bucket(
            Bucket=os.environ["SVEP_REGIONS"],
            CreateBucketConfiguration={
                "LocationConstraint": os.environ["AWS_DEFAULT_REGION"],
            },
        )

        yield setup_resources()
