#!/bin/bash
# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

. ./venv/bin/activate

set -euo pipefail

# seems to be circleCI specific
./venv/bin/pip3 install --upgrade pytest pytest-timeout pytest-runner pylama
./venv/bin/pip3 install --upgrade black
./venv/bin/pip3 install --upgrade pyre-check

./venv/bin/python3 setup-pylibra-beta.py develop

./venv/bin/python3 setup-pylibra-beta.py pytest --addopts="-W ignore::pytest.PytestDeprecationWarning --pylama tests $@"
./venv/bin/python3 -m black --check src tests
./venv/bin/pyre check
