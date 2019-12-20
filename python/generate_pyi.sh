#!/bin/bash -xv
source ./venv/bin/activate

set -euo pipefail

./venv/bin/pip3 install --upgrade mypy
# Don't work with cython yet
./venv/bin/stubgen -p pylibra.grpc --ignore-errors -v -o typeshed
