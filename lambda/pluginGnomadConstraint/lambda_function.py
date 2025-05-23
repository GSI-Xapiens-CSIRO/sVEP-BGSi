import json
import csv
import os
from collections import defaultdict

from shared.utils import (
    CheckedProcess,
    orchestration,
    Timer,
    download_to_tmp,
)

REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]
CONSTRAINT_REFERENCE = os.environ["CONSTRAINT_REFERENCE"]
GENE_INDEX_REFERENCE = os.environ["GENE_INDEX_REFERENCE"]

MAX_ROW_PER_CHUNK = 300
MILLISECONDS_BEFORE_SPLIT = 300000
CONSTRAINT_COLUMNS = {
    "misZ": 32,
    "misOe": 27,
    "misOeCiLower": 29,
    "misOeCiUpper": 30,
    "lofPli": 15,
    "lofOe": 13,
    "lofOeCiUpper": 19,
    "lofOeCiLower": 18,
}

download_to_tmp(REFERENCE_LOCATION, CONSTRAINT_REFERENCE, raise_on_notfound=True)
download_to_tmp(REFERENCE_LOCATION, GENE_INDEX_REFERENCE, raise_on_notfound=True)


def parse_value(val):
    try:
        return float(val)
    except ValueError:
        return val


def get_query_process(gene, index_file, constraint_file):
    results = []

    if gene in index_file:
        constraint_file.seek(index_file[gene])
        results = constraint_file.readlines()

    constraints_data = {}
    for result in results:
        line = result.strip()
        if not line:
            continue
        geneName, genId, transcript, *query_data = line.split("\t")
        if gene == geneName:
            constraints_data[transcript] = {
                key: parse_value(query_data[index])
                for key, index in CONSTRAINT_COLUMNS.items()
            }
        else:
            break
    return constraints_data


def convert_to_genes_queries(sns_data):
    genes_data = defaultdict(list)
    for data in sns_data:
        genes_data[data["geneName"]].append(data)
    return genes_data


def add_constraint_columns(sns_data, timer):
    genes_data = convert_to_genes_queries(sns_data)

    with open(f"/tmp/{GENE_INDEX_REFERENCE}") as injson:
        index_file = json.load(injson)

    lines_updated = 0
    completed_lines = []
    remaining_data = []

    with open(f"/tmp/{CONSTRAINT_REFERENCE}") as constraint_file:
        for gene, gene_datas in genes_data.items():

            constraint_info = get_query_process(gene, index_file, constraint_file)
            for i, data in enumerate(gene_datas):
                if timer.out_of_time():
                    remaining_data = gene_datas[i:] + [
                        item
                        for g, datas in list(genes_data.items())[
                            list(genes_data.keys()).index(gene) + 1 :
                        ]
                        for item in datas
                    ]
                    break
                transcript = data["transcriptId"].split(".")[0]
                if transcript in constraint_info:
                    data.update(constraint_info[transcript])
                    lines_updated += 1

            completed_lines.extend(gene_datas)

    print(
        f"Updated {lines_updated}/{len(completed_lines)} rows with Constraint Genomes data"
    )
    return completed_lines, remaining_data


def lambda_handler(event, context):
    timer = Timer(context, MILLISECONDS_BEFORE_SPLIT)
    with orchestration(event) as orc:
        sns_data = orc.message["snsData"]
        complete_lines, remaining = add_constraint_columns(sns_data, timer)
        if remaining:
            print(f"remaining data length {len(remaining)}")
            orc.resend_self(
                message_update={
                    "snsData": remaining,
                },
            )
            assert len(remaining) < len(
                sns_data
            ), "Not able to make any progress getting gnomAD data"
        orc.next_function(
            message={
                "snsData": complete_lines,
            },
        )
