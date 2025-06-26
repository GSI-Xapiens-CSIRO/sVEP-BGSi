import os

keys = {
    # aws
    "AWS_DEFAULT_REGION": "ap-southeast-2",
    # cognito
    "COGNITO_USER_POOL_ID": "COGNITO_USER_POOL_ID",
    "COGNITO_ADMIN_GROUP_NAME": "administrators",
    "COGNITO_REGISTRATION_EMAIL_LAMBDA": "COGNITO_REGISTRATION_EMAIL_LAMBDA",
    # svep
    "SVEP_TEMP": "svep-backend-temp-20250530000050167100000004",
    "COLUMNS": "rank,region,alt,consequence,varName,geneName,geneId,feature,transcriptId,transcriptBiotype,exonNumber,aminoAcids,codons,strand,transcriptSupportLevel,ref,gt,qual,filter,variationId,rsId,omimId,classification,conditions,clinSig,reviewStatus,lastEvaluated,accession,pubmed,afAfr,afEas,afFin,afNfe,afSas,afAmr,af,ac,an,siftMax,af1KG,afKhv,misZ,misOe,misOeCiLower,misOeCiUpper,lofPli,lofOe,lofOeCiUpper,lofOeCiLower",
    "SVEP_REGIONS": "svep-backend-regions-20250530000050131700000001",
    "AWS_LAMBDA_FUNCTION_NAME": "svep-backend-formatOutput",
}

# Set environment variables for testing
for key, value in keys.items():
    os.environ[key] = value
