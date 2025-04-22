import subprocess
import os
import boto3
import json
from uuid import uuid4
from shared.apiutils import bad_request, bundle_response
from shared.utils import get_sns_event, generate_presigned_get_url


s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

BUCKET_NAME = os.environ["FILE_LOCATION"]
RESULT_DURATION = int(os.environ["RESULT_DURATION"])

input_dir = "/tmp/input"
output_dir = "/tmp/output"
os.makedirs(input_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

def get_result_type(file_name):
    key_titles = {
        "qual-score-histogram": {
            "key": "qc_hc",
            "title": "Variant Quality Score Distributions",
        },
        "gq-score-histogram": {"key": "low_var", "title": "Low Variant Flagging"},
        "qual-score-vs-dp-scatterplot": {"key": "gq", "title": "Genotype Quality"},
        "allele-frequency": {"key": "alle_freq", "title": "Allele Frequency"},
        "number-of-substitutions-of-snps-passed": {
            "key": "snp_pass",
            "title": "Only with SNP's Pass all filters",
        },
    }

    for key, value in key_titles.items():
        if key in file_name:
            return value("key"), value.get("title")


def lambda_handler(event, context):
    event_body = event.get("body")

    if not event_body:
        return bad_request("No body sent with request.")

    try:
        body_dict = json.loads(event_body)
        project_name = body_dict["projectName"]
        file_name = body_dict["fileName"]
        input_vcf_file = f"projects/{project_name}/project-files/{file_name}"

        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"projects/{project_name}/qc-figures/{file_name}/",
        )
        if "Contents" in response:
            image_files = [obj["Key"] for obj in response["Contents"]]

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
            s3_resource.Bucket(BUCKET_NAME).download_file(input_vcf_file, input_dir)
            for vcf_file in os.listdir(input_dir):
                if vcf_file.endswith(".vcf"):
                    vcf_path = os.path.join(input_dir, vcf_file)
                    output_prefix = os.path.splitext(vcf_file)[0]
                    print(f"Processing: {vcf_file}")
                    if vcf_file.endswith(".vcf"):
                        vcf_path = os.path.join(input_dir, vcf_file)
                        output_prefix = os.path.splitext(vcf_file)[0]

                        print(f"Processing: {vcf_file}")

                        output_image = os.path.join(output_dir, f"{output_prefix}.png")
                        subprocess.run(
                            [
                                "vcfstats",
                                "--vcf",
                                vcf_path,
                                "--outdir",
                                output_dir,
                                "--formula",
                                "QUAL ~ 1",
                                "--title",
                                f"QUAL Score Histogram ({vcf_file})",
                            ],
                            check=True,
                            cwd="/tmp",
                        )
                        print(f"Results saved in: {output_image}")

                        subprocess.run(
                            [
                                "vcfstats",
                                "--vcf",
                                vcf_path,
                                "--outdir",
                                output_dir,
                                "--formula",
                                "GQs ~ 1",
                                "--title",
                                f"GQ Score Histogram ({vcf_file})",
                            ],
                            check=True,
                            cwd="/tmp",
                        )
                        print(f"Results saved in: {output_image}")

                        subprocess.run(
                            [
                                "vcfstats",
                                "--vcf",
                                vcf_path,
                                "--outdir",
                                output_dir,
                                "--formula",
                                "QUAL ~ DPs",
                                "--title",
                                f"QUAL Score vs DP Scatterplot ({vcf_file})",
                            ],
                            check=True,
                            cwd="/tmp",
                        )

                        print(f"Results saved in: {output_image}")

                        subprocess.run(
                            [
                                "vcfstats",
                                "--vcf",
                                vcf_path,
                                "--outdir",
                                output_dir,
                                "--formula",
                                "AAF ~ CONTIG",
                                "--title",
                                f"Allele Frequency ({vcf_file})",
                            ],
                            check=True,
                            cwd="/tmp",
                        )
                        print(f"Results saved in: {output_image}")

                        subprocess.run(
                            [
                                "vcfstats",
                                "--vcf",
                                vcf_path,
                                "--outdir",
                                output_dir,
                                "--formula",
                                "COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]",
                                "--title",
                                f"Number of substitutions of SNPs (passed) ({vcf_file})",
                                "--passed",
                            ],
                            check=True,
                            cwd="/tmp",
                        )

                        print(f"Results saved in: {output_image}")

                    if os.path.isfile(vcf_path):
                        os.unlink(vcf_path)

            images = {}

            for image_file in os.listdir(output_dir):
                image_path = os.path.join(output_dir, image_file)
                output_vcfstats_file = (
                    f"projects/{project_name}/qc-figures/{file_name}/{image_file}"
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
