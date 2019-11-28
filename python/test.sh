#!/bin/bash

. ./venv/bin/activate

set -euo pipefail

# seems to be circleCI specific
./venv/bin/pip3 install --upgrade pytest

mkdir -p ../tests-results/python
./venv/bin/python3 setup.py build_proto
./venv/bin/python3 setup.py pytest --addopts=" $@"
