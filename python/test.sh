#!/bin/bash

. ./venv/bin/activate

set -euo pipefail

# seems to be circleCI specific
./venv/bin/pip3 install --upgrade pytest
./venv/bin/pip3 install --upgrade black
./venv/bin/pip3 install --upgrade pyre-check

./venv/bin/python3 setup.py develop

./venv/bin/python3 setup.py pytest --addopts="--pylama . $@"
./venv/bin/python3 -m black --check .
./venv/bin/pyre check
