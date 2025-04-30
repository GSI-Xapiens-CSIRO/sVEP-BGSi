import json
from shared.dynamodb import scan_pending_jobs, bulk_delete_jobs


def lambda_handler(event, _):
    if event.get("source") == "aws.events":
        pending_jobs = scan_pending_jobs()

        print(f"[Crob Jobs] - Found {len(pending_jobs)} pending jobs to delete.")
        print(f"[Crob Jobs] - Pending jobs: {json.dumps(pending_jobs, default=str)}")

        if len(pending_jobs) > 0:
            print("[Crob Jobs] - Deleting pending jobs.")
            # Delete the pending jobs
            bulk_delete_jobs(pending_jobs)
