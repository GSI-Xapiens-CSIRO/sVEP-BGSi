set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR"

export PATH=$PATH:$SCRIPT_DIR/../layers/binaries/bin/
pytest -p no:warnings -vv ./test_format_output/
pytest -p no:warnings -vv ./test_plugin_gnomade_one_kg/