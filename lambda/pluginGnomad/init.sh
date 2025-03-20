#!/bin/bash
set -ex

# Define directories
REPOSITORY_DIRECTORY="${PWD}"
LIBRARIES="${REPOSITORY_DIRECTORY}/libraries"
SOURCE="${LIBRARIES}/source"

# Clean existing libraries
if [ -d "${LIBRARIES}" ]; then
  rm -rf "${LIBRARIES}"
fi

# Create necessary directories
mkdir -p "${LIBRARIES}"
mkdir -p "${SOURCE}"
mkdir -p layers/hail/python  # Use /python for AWS Lambda

# Create a virtual environment
cd ${SOURCE}
python3 -m venv hail_env
source hail_env/bin/activate

# Install dependencies
pip install --upgrade pip
pip install hail

# Copy installed packages to the Lambda layer
cp -r hail_env/lib/python*/site-packages/* ${REPOSITORY_DIRECTORY}/layers/hail/python/

# Deactivate virtual environment
deactivate

# Package Hail as a Lambda layer
cd ${REPOSITORY_DIRECTORY}/layers/hail
zip -r ../../hail-layer.zip .

echo "✅ Hail Lambda Layer built successfully!"
