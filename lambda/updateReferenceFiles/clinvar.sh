#!/bin/bash

set -exuo pipefail
trap 'shutdown -h now' EXIT

FTP_PATH="__FTP_PATH__"
CLINVAR_FILE="__CLINVAR_FILE__"
OUTPUT_BED="__OUTPUT_BED__"
REFERENCE_BUCKET="__REFERENCE_BUCKET__"

FULL_PATH="${FTP_PATH}/${CLINVAR_FILE}"

yum update -y
yum install -y \
    awscli \
    gcc \
    make \
    zlib-devel \

# Install htslib
HTSLIB_VERSION="1.21"
curl -L https://github.com/samtools/htslib/releases/download/$HTSLIB_VERSION/htslib-$HTSLIB_VERSION.tar.bz2 | tar -xjf -
cd htslib-$HTSLIB_VERSION
./configure  --disable-bz2 --disable-lzma
make install

cat > xmltobed.py << 'EOF'
__clinvar_xmltobed.py__
EOF

curl -O "${FULL_PATH}" --retry 9
curl -O "${FULL_PATH}.md5" --retry 9
# Remove preceeding path from md5 file
sed -i 's|\([a-f0-9]\+ \).*/|\1*|' "${CLINVAR_FILE}.md5"
md5sum -c "${CLINVAR_FILE}.md5"
bgzip -cd "${CLINVAR_FILE}" | python3 xmltobed.py | sort -k 1,1 -k 2,2n -k 3,3n | bgzip -c > "${OUTPUT_BED}"
tabix --csi "${OUTPUT_BED}"
aws s3 cp --recursive --exclude "*" --include "${OUTPUT_BED}*" . "s3://${REFERENCE_BUCKET}/"
