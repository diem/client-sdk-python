#!/bin/bash
# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

. ./venv/bin/activate

set -euo pipefail

# seems to be circleCI specific
./venv/bin/pip3 install --upgrade pytest pytest-timeout pytest-runner pylama
./venv/bin/pip3 install --upgrade black
./venv/bin/pip3 install --upgrade pyre-check

./venv/bin/python3 setup.py develop

./venv/bin/python3 setup.py pytest --addopts="-W ignore::pytest.PytestDeprecationWarning --pylama . $@"
./venv/bin/python3 -m black --check .
./venv/bin/pyre check
