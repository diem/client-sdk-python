#!/bin/bash -xv

python3 -m venv ./venv
. ./venv/bin/activate

set -euo pipefail

./venv/bin/pip3 install --upgrade pip

./venv/bin/python3 setup.py download_proto
./venv/bin/python3 setup.py develop
