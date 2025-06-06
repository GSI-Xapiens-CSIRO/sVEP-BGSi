import json
import os

import boto3


CLINVAR_FTP_PATH = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xml/weekly_release"
CLINVAR_FTP_FILE = "ClinVarVCVRelease_00-latest_weekly.xml.gz"
OUTPUT_BED = "clinvar.bed.gz"
EC2_IAM_INSTANCE_PROFILE = os.environ["EC2_IAM_INSTANCE_PROFILE"]
REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]
AWS_REGION = os.environ["AWS_REGION"]
FUNCTION_NAME = os.environ["AWS_LAMBDA_FUNCTION_NAME"]
DYNAMO_SVEP_REFERENCES_TABLE = os.environ["DYNAMO_SVEP_REFERENCES_TABLE"]

REGION_AMI_MAP = {
    "ap-southeast-2": "ami-0822a7a2356687b0f",
    "ap-southeast-3": "ami-0f6fd501d5bfeb733",
}


def update_clinvar(clinvar_version):
    ec2_client = boto3.client("ec2")
    ami = REGION_AMI_MAP[AWS_REGION]
    device_name = ec2_client.describe_images(ImageIds=[ami])["Images"][0][
        "RootDeviceName"
    ]

    with open("clinvar_xmltobed.py") as processing_file:
        clinvar_xmltobed = processing_file.read()

    with open("clinvar.sh") as user_data_file:
        ec2_startup = (
            user_data_file.read()
            .replace("__FTP_PATH__", CLINVAR_FTP_PATH)
            .replace("__CLINVAR_FILE__", CLINVAR_FTP_FILE)
            .replace("__OUTPUT_BED__", OUTPUT_BED)
            .replace("__REFERENCE_BUCKET__", REFERENCE_LOCATION)
            .replace("__clinvar_xmltobed.py__", clinvar_xmltobed)
            .replace("__REGION__", AWS_REGION)
            .replace("__TABLE__", DYNAMO_SVEP_REFERENCES_TABLE)
            .replace("__ID__", "clinvar_version")
            .replace("__VERSION__", clinvar_version)
        )
    try:
        # Launch EC2 instance
        response = ec2_client.run_instances(
            ImageId=REGION_AMI_MAP[AWS_REGION],
            InstanceType="m5.large",
            MinCount=1,
            MaxCount=1,
            BlockDeviceMappings=[
                {
                    "DeviceName": device_name,
                    "Ebs": {
                        "DeleteOnTermination": True,
                        "VolumeSize": 24,
                        "VolumeType": "gp3",
                        "Encrypted": True,
                    },
                },
            ],
            UserData=ec2_startup,
            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": f"{FUNCTION_NAME}-clinvar"}],
                }
            ],
            IamInstanceProfile={"Name": EC2_IAM_INSTANCE_PROFILE},
        )
        instance_id = response["Instances"][0]["InstanceId"]
    except Exception as e:
        print(f"Error launching EC2 instance: {str(e)}")
        return {"statusCode": 500, "body": json.dumps("Error launching EC2 instance")}
    print(f"Launched EC2 instance {instance_id} To create clinvar reference")
    return {
        "statusCode": 200,
        "body": json.dumps(f"Launched EC2 instance {instance_id}"),
    }
