#!/bin/bash

set -exuo pipefail

FTP_PATH="https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xml/weekly_release"
CLINVAR_FILE="ClinVarVCVRelease_00-latest_weekly.xml.gz"
OUTPUT_BED="clinvar.bed.gz"

wget "${FTP_PATH}/${CLINVAR_FILE}"
wget "${FTP_PATH}/${CLINVAR_FILE}.md5"
# Remove preceeding path from md5 file
sed -i 's|\([a-f0-9]\+ \*\).*/|\1|' "${CLINVAR_FILE}.md5"
md5sum -c "${CLINVAR_FILE}.md5"
bgzip -cd "${CLINVAR_FILE}" | python3 xmltobed.py | sort -k 1,1 -k 2,2n -k 3,3n | bgzip -c > "${OUTPUT_BED}"
tabix --csi "${OUTPUT_BED}"
