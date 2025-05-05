from shared.utils import orchestration


def lambda_handler(event, _):
    with orchestration(event) as orc:
        total_coords = orc.message["coords"]
        print(f"length = {len(total_coords)}")
        for sub_coords in total_coords:
            orc.next_function(
                message={
                    "coords": sub_coords,
                },
            )
