#!/bin/bash -xv
# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

. ./venv/bin/activate

set -euo pipefail
./venv/bin/pip install --upgrade twine

rm dist/* || true
./venv/bin/python3 setup.py sdist

export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-AgENdGVzdC5weXBpLm9yZwIkNGVmMTllNDUtMjM1Yi00YTVhLWJkNWYtZDBhYzc5NjZhMmEwAAIleyJwZXJtaXNzaW9ucyI6ICJ1c2VyIiwgInZlcnNpb24iOiAxfQAABiC54pvKHX1RI4wSUk7rWKLw5abBSH0HtWKWBygC1PXaPw"
./venv/bin/python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
