import subprocess
import os
import boto3
import json
from uuid import uuid4
from shared.apiutils import bad_request, bundle_response
from shared.utils import get_sns_event, generate_presigned_get_url, _gzip_dc


s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

BUCKET_NAME = os.environ["FILE_LOCATION"]
RESULT_DURATION = int(os.environ["RESULT_DURATION"])

input_dir = "/tmp/input"
output_dir = "/tmp/output"
os.makedirs(input_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

mapping_formula = {
    "qc_hc": {
        "formula": "QUAL ~ 1",
        "title": "Variant Quality Score Distributions",
        "image_title": "QUAL Score Histogram",
        "identifier": "qual-score-histogram",
    },
    "low_var": {
        "formula": "GQs ~ 1",
        "title": "Low Variant Flagging",
        "image_title": f"GQ Score Histogram",
        "identifier": "gq-score-histogram",
    },
    "gq": {
        "formula": "QUAL ~ DPs",
        "title": "Genotype Quality",
        "image_title": f"QUAL Score vs DP Scatterplot",
        "identifier": "qual-score-vs-dp-scatterplot",
    },
    "alle_freq": {
        "formula": "AAF ~ CONTIG",
        "title": "Allele Frequency",
        "image_title": f"Allele Frequency",
        "identifier": "allele-frequency",
    },
    "snp_pass": {
        "formula": "COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]",
        "title": "Only with SNP's Pass all filters",
        "image_title": f"Number of substitutions of SNPs (passed)",
        "identifier": "number-of-substitutions-of-snps-passed",
    },
}


def get_result_type(file_name):
    for key, value in mapping_formula.items():
        identifier = value['identifier']
        if identifier in file_name:
            return key, value["title"]


def get_formula_and_title(key, vcf_file):
    formula = mapping_formula.get(key, False)
    if not formula:
        return False, False
    return formula["formula"], f"{formula["image_title"]} ({vcf_file})"


def lambda_handler(event, context):
    event_body = event.get("body")

    if not event_body:
        return bad_request("No body sent with request.")

    try:
        body_dict = json.loads(event_body)
        project_name = body_dict["projectName"]
        file_name = body_dict["fileName"]
        key = body_dict["key"]
        input_vcf_file = f"projects/{project_name}/project-files/{file_name}"
        local_vcf_path = os.path.join(input_dir, os.path.basename(file_name))

        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"projects/{project_name}/qc-figures/{file_name}/",
        )

        contents = response and "Contents" in response
        image_files = contents and [obj["Key"] for obj in response["Contents"]]
        formula = mapping_formula.get(key,False)
        if not formula:
            return bundle_response(
                        400,
                        {
                            "message": "Formula not found. Please check key parameter.",
                            "images": {},
                        },
                    )
        identifier = formula['identifier']
        if any(identifier in image_file for image_file in image_files):
            print("get existing Images")
            print(response)

            images = {}
            for image_file in image_files:
                output_vcfstats_file = (
                    f"projects/{project_name}/qc-figures/{file_name}/{image_file}"
                )

                result_url = generate_presigned_get_url(
                    BUCKET_NAME,
                    output_vcfstats_file,
                    RESULT_DURATION,
                )
                key, title = get_result_type(image_file)

                images[key] = {
                    "title": title,
                    "url": result_url,
                }

            return bundle_response(
                200,
                {
                    "message": "Image generated and uploaded successfully",
                    "images": images,
                },
            )
        else:
            s3_resource.Bucket(BUCKET_NAME).download_file(
                input_vcf_file, local_vcf_path
            )
            for vcf_file in os.listdir(input_dir):
                if vcf_file.endswith(".vcf.gz"):
                    vcf_path = os.path.join(input_dir, vcf_file)
                    output_prefix = os.path.splitext(vcf_file)[0]
                    print(f"Processing: {vcf_file}")
                    if vcf_file.endswith(".vcf.gz"):
                        vcf_path = os.path.join(input_dir, vcf_file)
                        output_prefix = os.path.splitext(vcf_file)[0]

                        print(f"Processing: {vcf_file}")

                        output_image = os.path.join(output_dir, f"{output_prefix}.png")
                        formula, image_title = get_formula_and_title(key, vcf_file)
                        if not formula:
                            return bundle_response(
                                400,
                                {
                                    "message": "Formula not found. Please check key parameter.",
                                    "images": {},
                                },
                            )

                        vcfstats_params = [
                            "vcfstats",
                            "--vcf",
                            vcf_path,
                            "--outdir",
                            output_dir,
                            "--formula",
                            formula,
                            "--title",
                            image_title,
                        ]

                        if key == "snp_pass":
                            vcfstats_params.append("--passed")

                        subprocess.run(
                            vcfstats_params,
                            check=True,
                            cwd="/tmp",
                        )
                        print(f"Results saved in: {output_image}")

                if os.path.isfile(vcf_path):
                    os.unlink(vcf_path)

            images = {}
            for image_file_name in os.listdir(output_dir):
                image_path = os.path.join(output_dir, image_file_name)
                output_vcfstats_file = (
                    f"projects/{project_name}/qc-figures/{file_name}/{image_file_name}"
                )
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=output_vcfstats_file,
                    Body=image_data,
                    ContentType="image/png",
                )
                if os.path.isfile(image_path):
                    os.unlink(image_path)

                result_url = generate_presigned_get_url(
                    BUCKET_NAME,
                    output_vcfstats_file,
                    RESULT_DURATION,
                )
                key, title = get_result_type(image_file_name)

                images[key] = {
                    "title": title,
                    "url": result_url,
                }

            return bundle_response(
                200,
                {
                    "message": "Image generated and uploaded successfully",
                    "images": images,
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
