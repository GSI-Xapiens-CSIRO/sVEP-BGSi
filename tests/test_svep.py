from unittest.mock import patch

import botocore
from moto import mock_aws

orig = botocore.client.BaseClient._make_api_call


def mock_make_api_call(self, operation_name, kwarg):

    return orig(self, operation_name, kwarg)


def test_svep_formatoutput(resources_dict):
    import lambda_function

    with patch(
        "botocore.client.BaseClient._make_api_call",
        new=mock_make_api_call,
    ):
        event = {
            "Records": [
                {
                    "Sns": {
                        "TopicArn": "arn:aws:sns:ap-southeast-2:735408665664:svep-backend-formatOutput",
                        "Message": '{"snsData": [{"transcriptId": "ENST00000362061.4", "ref": "C", "region": "chr1:201060815-201060815", "chrom": "chr1", "transcriptSupportLevel": "1", "exonNumber": "26", "filter": "PASS", "dbIds": ".|.|OMIM:170400;MONDO:0008223;ORPHA:681|HGNC:1397;OMIM:114208|medgen:356151;OMIM:601887;MONDO:0011163", "altVcf": "T", "strand": -1, "alt": "T", "codons": "cGc/cAc", "consequence": "missense_variant,splice_region_variant", "geneId": "ENSG00000081248", "rank": 12, "posVcf": 201060815, "geneName": "CACNA1S", "transcriptBiotype": "protein_coding", "refVcf": "C", "gt": "0/1", "aminoAcids": "R/H", "qual": ".", "feature": "transcript", "variationId": "17626", "varName": "NM_000069.3(CACNA1S):c.3257G>A (p.Arg1086His)", "rsId": "rs1800559", "omimId": "114208.0004", "classification": "Germline", "conditions": "Hypokalemic periodic paralysis, type 1, Malignant hyperthermia, susceptibility to, 5", "clinSig": "Pathogenic", "reviewStatus": "criteria provided, single submitter", "lastEvaluated": "2022-01-17", "accession": "RCV001851936", "pubmed": "20298421,11260227,20213496,31851124,9199552,34012068,20431982,28011884,22992668,20301512,15201141,16163667,28492532,12411788,25741868,26188342,20301325,35802134,33131754", "misZ": 1.3387, "misOe": 0.92687, "misOeCiLower": 0.895, "misOeCiUpper": 0.959, "lofPli": 6.2927e-18, "lofOe": 0.558, "lofOeCiUpper": 0.651, "lofOeCiLower": 0.479}, {"transcriptId": "ENST00000362061.4", "ref": "C", "region": "chr1:201060815-201060815", "chrom": "chr1", "transcriptSupportLevel": "1", "exonNumber": "26", "filter": "PASS", "dbIds": ".|.", "altVcf": "T", "strand": -1, "alt": "T", "codons": "cGc/cAc", "consequence": "missense_variant,splice_region_variant", "geneId": "ENSG00000081248", "rank": 12, "posVcf": 201060815, "geneName": "CACNA1S", "transcriptBiotype": "protein_coding", "refVcf": "C", "gt": "0/1", "aminoAcids": "R/H", "qual": ".", "feature": "transcript", "variationId": "17626", "varName": "NM_000069.3(CACNA1S):c.3257G>A (p.Arg1086His)", "rsId": "rs1800559", "omimId": "114208.0004", "classification": "Germline", "conditions": "Malignant hyperthermia, susceptibility to, 5", "clinSig": "Pathogenic", "reviewStatus": "criteria provided, multiple submitters, no conflicts", "lastEvaluated": "2023-08-01", "accession": "RCV000019193", "pubmed": "20298421,11260227,20213496,31851124,9199552,34012068,20431982,28011884,22992668,20301512,15201141,16163667,28492532,12411788,25741868,26188342,20301325,35802134,33131754", "misZ": 1.3387, "misOe": 0.92687, "misOeCiLower": 0.895, "misOeCiUpper": 0.959, "lofPli": 6.2927e-18, "lofOe": 0.558, "lofOeCiUpper": 0.651, "lofOeCiLower": 0.479}], "requestId": "3c79842a-e94f-4f70-8bf8-6c382de6f9aa", "refChrom": "1", "tempFileName": "3c79842a-e94f-4f70-8bf8-6c382de6f9aa_0_svep-backend-queryVCF_chr1_200_0_0_svep-backend-queryGTF_0_svep-backend-pluginConsequence_svep-backend-pluginClinvar_0_svep-backend-pluginGnomad_0_svep-backend-pluginGnomadOneKG_0_svep-backend-pluginGnomadConstraint_0_svep-backend-formatOutput"}',
                    }
                }
            ]
        }

        lambda_function.lambda_handler(
            event,
            {},
        )
