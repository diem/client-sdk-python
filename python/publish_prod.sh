#!/bin/bash -xv
# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

. ./venv/bin/activate

set -euo pipefail
./venv/bin/pip install --upgrade twine

rm dist/* || true
./venv/bin/python3 setup.py sdist

export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-AgEIcHlwaS5vcmcCJDgyMWY1MDFiLTg5MzItNDQyYy1iMjFjLWRiNjg3YjAwMTRjNQACJXsicGVybWlzc2lvbnMiOiAidXNlciIsICJ2ZXJzaW9uIjogMX0AAAYgWL8qVeVlUrHyNmfy0DRtwB9tk7AZW9pHvWckl8UsveU"
./venv/bin/python3 -m twine upload dist/*


