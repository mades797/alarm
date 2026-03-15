#!/bin/bash

ROOT="$(dirname "$(realpath "$0")")"

source .venv/bin/activate

export PYTHONPATH="${ROOT}"

pytest "${ROOT}/tests/tests.py" --cov="${ROOT}"
