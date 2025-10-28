#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

VENV_DIR="$SCRIPT_DIR/../.venv"
PYTHON_SCRIPT="$SCRIPT_DIR/../src/main.py"

source "$VENV_DIR/bin/activate"
python "$PYTHON_SCRIPT" "$@"

deactivate
