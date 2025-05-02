from collections import Counter
from contextlib import contextmanager
import os
import shutil
import json
import math
import subprocess
import traceback

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from shared.dynamodb import query_clinic_job, update_clinic_job

# Optional environment variables
SVEP_TEMP = os.environ.get("SVEP_TEMP")
REGION = os.environ.get("REGION")

# AWS clients and resources
s3 = boto3.resource("s3")
sns = boto3.client("sns")
s3_client = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)

MAX_PRINT_LENGTH = 1024
MAX_SNS_EVENT_PRINT_LENGTH = 2048
MAX_SNS_MESSAGE_SIZE = 260000
S3_PAYLOAD_KEY = "_s3_payload_key"
TEMP_FILE_FIELD = "tempFileName"
REQUEST_ID_FIELD = "requestId"
REF_CHROM_FIELD = "refChrom"
RESERVED_FIELDS = {
    TEMP_FILE_FIELD,
    REQUEST_ID_FIELD,
    REF_CHROM_FIELD,
}


class Timer:
    def __init__(self, context, buffer_time):
        self.context = context
        self.buffer_time = buffer_time

    def out_of_time(self):
        return self.context.get_remaining_time_in_millis() <= self.buffer_time


class Orchestrator:
    def __init__(self, event=None, request_id=None):
        self.function_calls = Counter()
        self.resent = False
        if event is not None:
            self.message = get_sns_event(event)
            self.topic_arn = event["Records"][0]["Sns"]["TopicArn"]
            self.ref_chrom = self.message.get(REF_CHROM_FIELD)
            self.temp_file_name = self.message[TEMP_FILE_FIELD]
            if self.temp_file_name.startswith("_"):
                self.track = False
                self.temp_file_name = self.temp_file_name[1:]
            else:
                self.track = True
            self.request_id = self.message[REQUEST_ID_FIELD]
        else:
            # Not created from upstream SNS, i.e. initQuery
            self.message = None
            self.topic_arn = None
            self.ref_chrom = None
            self.request_id = request_id
            self.temp_file_name = request_id
            self.track = False

    def resend_self(self, message_update=None, max_length=MAX_PRINT_LENGTH):
        self._check_reserved_fields(message_update)
        assert self.topic_arn is not None, "Cannot resend a non-SNS function."
        assert not self.resent, "Can only resend once per invocation."
        function_name = _get_function_name_from_arn(self.topic_arn)
        base_name, old_index = self.temp_file_name.rsplit(function_name, 1)
        old_index = old_index or 0  # Account for empty string
        filename = f"{base_name}{function_name}{int(old_index) + 1}"
        message = (
            (self.message | message_update)
            if message_update is not None
            else self.message
        )
        self._start_function_with_filename(
            self.topic_arn, message, filename, self.track, max_length
        )
        self.resent = True

    def start_function(
        self, topic_arn, message, suffix=None, track=True, max_length=MAX_PRINT_LENGTH
    ):
        self._check_reserved_fields(message)
        base_filename = (
            f"{self.temp_file_name}_{suffix}" if suffix else self.temp_file_name
        )
        function_name = _get_function_name_from_arn(topic_arn)
        function_key = f"{base_filename}_{function_name}"
        filename = (
            f"{base_filename}_{self.function_calls[function_key]}_{function_name}"
        )
        self.function_calls[function_key] += 1
        self._start_function_with_filename(
            topic_arn, message, filename, track, max_length
        )

    def _check_reserved_fields(self, message):
        for field in RESERVED_FIELDS:
            if field in message:
                raise ValueError(f"Field {field} is set by the orchestrator.")

    def _start_function_with_filename(
        self, topic_arn, message, filename, track, max_length
    ):
        message[REQUEST_ID_FIELD] = self.request_id
        if self.ref_chrom is not None:
            message[REF_CHROM_FIELD] = self.ref_chrom
        if track:
            _create_temp_file(filename)
        else:
            filename = f"_{filename}"
        message[TEMP_FILE_FIELD] = filename
        sns_publish(topic_arn, message, max_length, filename)

    def _mark_completed(self):
        if self.track:
            print(f"Deleting file: {self.temp_file_name}")
            s3.Object(SVEP_TEMP, self.temp_file_name).delete()


@contextmanager
def orchestration(event=None, request_id=None):
    orchestrator = Orchestrator(event, request_id)
    try:
        yield orchestrator
        orchestrator._mark_completed()
        print("Completed successfully.")
    except Exception as e:
        handle_failed_execution(orchestrator.request_id, e)
        print("Completed unsuccessfully.")


class ProcessError(Exception):
    def __init__(self, message, stdout, stderr, returncode, process_args):
        self.message = message
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.process_args = process_args
        super().__init__(message)

    def __str__(self):
        return f"{self.message}\nProcess args: {self.process_args}\nstderr:\n{self.stderr}\nreturncode: {self.returncode}"


class CheckedProcess:
    def __init__(self, args, error_message=None, **kwargs):
        defaults = {
            "args": args,
            "stderr": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "cwd": "/tmp",
            "encoding": "utf-8",
        }
        kwargs.update({k: v for k, v in defaults.items() if k not in kwargs})
        print(
            f"Running subprocess.Popen with kwargs: {json.dumps(kwargs, default=str)}"
        )
        self.process = subprocess.Popen(**kwargs)
        self.error_message = error_message or f"Error running {args[0]}"
        self.stdout = self.process.stdout
        self.stdin = self.process.stdin

    def check(self):
        stdout, stderr = self.process.communicate()
        returncode = self.process.returncode
        if returncode != 0:
            raise ProcessError(
                self.error_message, stdout, stderr, returncode, self.process.args
            )


def _get_function_name_from_arn(arn):
    return arn.split(":")[-1]


def _truncate_string(string, max_length=MAX_PRINT_LENGTH):
    length = len(string)

    if (max_length is None) or (length <= max_length):
        return string

    excess_bytes = length - max_length
    # Excess bytes + 9 for the smallest possible placeholder
    min_removed = excess_bytes + 9
    placeholder_chars = 8 + math.ceil(math.log(min_removed, 10))
    removed_chars = excess_bytes + placeholder_chars
    while True:
        placeholder = f"<{removed_chars} bytes>"
        # Handle edge cases where the placeholder gets larger
        # when characters are removed.
        total_reduction = removed_chars - len(placeholder)
        if total_reduction < excess_bytes:
            removed_chars += 1
        else:
            break
    if removed_chars > length:
        # Handle edge cases where the placeholder is larger than
        # maximum length. In this case, just truncate the string.
        return string[:max_length]
    snip_start = (length - removed_chars) // 2
    snip_end = snip_start + removed_chars
    # Cut out the middle of the string and replace it with the
    # placeholder.
    return f"{string[:snip_start]}{placeholder}{string[snip_end:]}"


def generate_presigned_get_url(bucket, key, expires=3600):
    kwargs = {
        "ClientMethod": "get_object",
        "Params": {
            "Bucket": bucket,
            "Key": key,
        },
        "ExpiresIn": expires,
    }
    print(f"Calling s3.generate_presigned_url with kwargs: {json.dumps(kwargs)}")
    response = s3_client.generate_presigned_url(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")
    return response


def download_to_tmp(bucket, key, raise_on_notfound=False):
    local_file_name = f"/tmp/{key}"
    try:
        s3.Bucket(bucket).download_file(key, local_file_name)
    except ClientError as error:
        if error.response["Error"]["Code"] == "404" and not raise_on_notfound:
            return False
        else:
            raise error
    return True


def download_vcf(bucket, vcf):
    download_to_tmp(bucket, vcf, raise_on_notfound=True)
    if not download_to_tmp(bucket, f"{vcf}.csi"):
        download_to_tmp(bucket, f"{vcf}.tbi", raise_on_notfound=True)


def download_bedfile(bucket, bedfile):
    download_to_tmp(bucket, bedfile, raise_on_notfound=True)
    if not download_to_tmp(bucket, f"{bedfile}.csi"):
        download_to_tmp(bucket, f"{bedfile}.tbi", raise_on_notfound=True)


def _create_temp_file(filename):
    print(f"Creating file: {filename}")
    s3.Object(SVEP_TEMP, filename).put(Body=b"")


def clear_tmp():
    for file_name in os.listdir("/tmp"):
        file_path = f"/tmp/{file_name}"
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def print_event(event, max_length=MAX_PRINT_LENGTH):
    truncated_print(f"Event Received: {json.dumps(event)}", max_length)


def get_sns_event(event, max_length=MAX_SNS_EVENT_PRINT_LENGTH):
    print_event(event, max_length)
    message = json.loads(event["Records"][0]["Sns"]["Message"])
    if (payload_key := message.get(S3_PAYLOAD_KEY)) is not None:
        print(f"Loading payload from S3 bucket {SVEP_TEMP} and key: {payload_key}")
        payload = s3.Object(SVEP_TEMP, payload_key).get()
        message = json.loads(payload["Body"].read().decode())
        truncated_print(f"Payload from S3: {json.dumps(message)}", max_length)
    return message


def sns_publish(
    topic_arn, message, max_length=MAX_PRINT_LENGTH, s3_payload_prefix=None
):
    message = json.dumps(message, separators=(",", ":"))
    if len(message) > MAX_SNS_MESSAGE_SIZE and s3_payload_prefix is not None:
        print(f"SNS message too large ({len(message)} bytes), uploading to S3")
        payload_key = f"payloads/{s3_payload_prefix}.json"
        truncated_print(
            f"Uploading to S3 bucket {SVEP_TEMP} and key {payload_key}: {message}",
            max_length,
        )
        s3.Object(SVEP_TEMP, payload_key).put(Body=message.encode())
        message = json.dumps({S3_PAYLOAD_KEY: payload_key}, separators=(",", ":"))
    kwargs = {
        "TopicArn": topic_arn,
        "Message": message,
    }
    truncated_print(f"Publishing to SNS: {json.dumps(kwargs)}", max_length)
    sns.publish(**kwargs)


def truncated_print(string, max_length=MAX_PRINT_LENGTH):
    if max_length is not None:
        string = _truncate_string(string, max_length)
        assert len(string) <= max_length
    print(string)


def handle_failed_execution(job_id, error_message):
    print(traceback.format_exc())
    job = query_clinic_job(job_id)
    if job.get("job_status").get("S") == "failed":
        return
    job_status = "failed"
    failed_step = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown")

    update_clinic_job(
        job_id,
        job_status=job_status,
        failed_step=failed_step,
        error_message=str(error_message),
        project_name=job.get("project_name", {}).get("S"),
        input_vcf=job.get("input_vcf", {}).get("S"),
        user_id=job.get("uid", {}).get("S"),
        is_from_failed_execution=True,
    )
