import os


from shared.utils import orchestration


# Environment variables
QUERY_GTF_SNS_TOPIC_ARN = os.environ["QUERY_GTF_SNS_TOPIC_ARN"]


def lambda_handler(event, _):
    with orchestration(event) as orc:
        total_coords = orc.message["coords"]
        print(f"length = {len(total_coords)}")
        for idx in range(len(total_coords)):
            orc.start_function(
                topic_arn=QUERY_GTF_SNS_TOPIC_ARN,
                message={
                    "coords": total_coords[idx],
                },
            )
