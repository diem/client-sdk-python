#!/bin/bash

. ./venv/bin/activate

set -euo pipefail

# seems to be circleCI specific
./venv/bin/pip3 install --upgrade pytest
./venv/bin/pip3 install --upgrade black
./venv/bin/pip3 install --upgrade pyre-check==0.0.41

./venv/bin/python3 setup.py develop

./venv/bin/python3 setup.py pytest --addopts="--runxfail --pylama . $@"
./venv/bin/black --check .
./venv/bin/pyre check
