import json
import os

from shared.apiutils import bad_request, bundle_response
from shared.utils import chrom_matching, print_event, sns_publish, start_function


# Environment variables
CONCAT_STARTER_SNS_TOPIC_ARN = os.environ['CONCAT_STARTER_SNS_TOPIC_ARN']
QUERY_VCF_SNS_TOPIC_ARN = os.environ['QUERY_VCF_SNS_TOPIC_ARN']
RESULT_DURATION = int(os.environ['RESULT_DURATION'])
RESULT_SUFFIX = os.environ['RESULT_SUFFIX']
SLICE_SIZE_MBP = int(os.environ['SLICE_SIZE_MBP'])
os.environ['PATH'] += f':{os.environ["LAMBDA_TASK_ROOT"]}'

REGIONS = chrom_matching.get_regions(SLICE_SIZE_MBP)


def get_translated_regions_and_mapping(location):
    vcf_chromosomes = chrom_matching.get_vcf_chromosomes(location)
    vcf_regions = []
    for target_chromosome, region_list in REGIONS.items():
        chromosome = chrom_matching.get_matching_chromosome(vcf_chromosomes,
                                                            target_chromosome)
        if not chromosome:
            raise ValueError(f"No matching chromosome found for '{target_chromosome}'")
        vcf_regions += [
            f'{chromosome}:{region}'
            for region in region_list
        ]
    chrom_mapping = chrom_matching.get_chromosome_mapping(vcf_chromosomes) 
    return vcf_regions, chrom_mapping


def lambda_handler(event, _):
    print_event(event, max_length=None)
    event_body = event.get('body')
    if not event_body:
        return bad_request("No body sent with request.")
    try:
        body_dict = json.loads(event_body)
        request_id = event['requestContext']['requestId']
        user_id = body_dict['userId']
        location = body_dict['location']
        vcf_regions, chrom_mapping = get_translated_regions_and_mapping(location)
    except json.JSONDecodeError:
        return bad_request("Error parsing request body, Expected JSON.")
    except ValueError as e:
        return bad_request(e)

    print(vcf_regions)
    start_function(QUERY_VCF_SNS_TOPIC_ARN, request_id, {
        'regions': vcf_regions,
        'location': location,
        'mapping': chrom_mapping,
    })
    sns_publish(CONCAT_STARTER_SNS_TOPIC_ARN, {
        'requestId': request_id,
        'userId': user_id,
    })

    return bundle_response(200, {
        "Response": "Process started",
        "RequestId": request_id,
    })
