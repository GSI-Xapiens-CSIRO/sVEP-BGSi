import json
import os
import gzip
import base64
import hail as hl

# ✅ Explicitly set Java home for Hail (important for AWS Lambda)
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-11-amazon-corretto"
os.environ["PATH"] = f"{os.environ['JAVA_HOME']}/bin:{os.environ['PATH']}"

# ✅ Set Spark configuration for AWS Lambda
hl.init(
    spark_conf={
        "spark.executor.memory": "2g",
        "spark.driver.memory": "2g",
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        "spark.sql.files.ignoreCorruptFiles": "true",
        "spark.sql.execution.arrow.pyspark.enabled": "true",
    }
)


def decompress_sns_data(encoded_data: str) -> str:
    compressed = base64.b64decode(encoded_data)  # Decode from Base64
    return gzip.decompress(compressed).decode("utf-8")  # Decompress with gzip


def lambda_handler(event, _):
    message = json.loads(event["Records"][0]["Sns"]["Message"])

    sns_data = message["snsData"]
    chrom_mapping = message["mapping"]
    request_id = message["requestId"]

    print("SNS data: ", sns_data)
    print("Chrom mapping: ", chrom_mapping)

    rows = [row.split("\t") for row in sns_data.split("\n") if row]
