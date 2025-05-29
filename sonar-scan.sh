#!/bin/bash

# === CONFIGURATION ===
SONAR_HOST_URL="https://16.79.20.54:9000"
SONAR_TOKEN="sqa_6b8f8df263ddb5d2f2bc4fa6f7439f8266fb8965"
PROJECT_DIR=$(pwd)

# === Log variables to debug ===
echo "SONAR_HOST_URL=${SONAR_HOST_URL}"
echo "SONAR_TOKEN=${SONAR_TOKEN}"
echo "PROJECT_DIR=${PROJECT_DIR}"

# === RUN SONAR SCANNER DOCKER ===
docker run --rm \
    -e SONAR_HOST_URL="${SONAR_HOST_URL}" \
    -e SONAR_TOKEN="${SONAR_TOKEN}" \
    -v "${PROJECT_DIR}:/usr/src" \
    sonarsource/sonar-scanner-cli