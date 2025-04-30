import json
from shared.dynamodb import scan_pending_jobs, bulk_delete_jobs, send_job_email
import time


def lambda_handler(event, _):
    if event.get("source") == "aws.events":
        pending_jobs = scan_pending_jobs()

        print(f"[Crob Jobs] - Found {len(pending_jobs)} pending jobs to delete.")
        print(f"[Crob Jobs] - Pending jobs: {json.dumps(pending_jobs, default=str)}")

        if len(pending_jobs) > 0:
            print("[Crob Jobs] - Deleting pending jobs.")
            # Delete the pending jobs
            # bulk_delete_jobs(pending_jobs)

            for job in pending_jobs:
                job_id = job["job_id"]["S"]
                user_id = job.get("uid", {}).get("S")
                project_name = job.get("project_name", {}).get("S")
                input_vcf = job.get("input_vcf", {}).get("S")
                job_status = job.get("job_status", {}).get("S")

                print(
                    f"[Crob Jobs] - Sending email for job {job_id} to user {user_id}."
                )

                send_job_email(
                    job_id=job_id,
                    job_status=job_status,
                    project_name=project_name,
                    input_vcf=input_vcf,
                    user_id=user_id,
                    is_from_failed_execution=True,  # Set true to avoid re running query_clinic_job
                )

                time.sleep(0.5)  # 500 milliseconds
