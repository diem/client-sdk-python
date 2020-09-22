#!/bin/bash -xv

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

python3 -m venv ./venv
source ./venv/bin/activate

set -euo pipefail

./venv/bin/pip3 install --upgrade pip

./venv/bin/python3 setup.py develop
./venv/bin/python3 setup-pylibra-beta.py develop
