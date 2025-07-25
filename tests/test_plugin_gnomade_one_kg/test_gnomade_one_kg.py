import os

import boto3


def test_svep_formatoutput(resources_dict):
    import lambda_function

    sns_data = [{"posVcf": 80113242, "refVcf": "G", "altVcf": "A"}]
    ref_chrom = "17"
    timer = type("DummyTimer", (), {"out_of_time": lambda self: False})()

    result = lambda_function.add_1kg_columns(sns_data, ref_chrom, timer)

    assert result == (
        [
            {
                "ac1KG": "562",
                "posVcf": 80113242,
                "refVcf": "G",
                "altVcf": "A",
                "an1KG": "6760",
                "af1KG": "0.0831361",
                "afKhv": "0.232673",
            }
        ],
        [],
    ), "Expected result does not match the actual result."
