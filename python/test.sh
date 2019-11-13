#!/bin/bash -xv
set -euo pipefail

python3 -m venv ./venv

./venv/bin/pip3 install --upgrade pip
./venv/bin/pip3 install --upgrade pytest cython

./venv/bin/python3 setup.py develop
./venv/bin/python3 setup.py pytest