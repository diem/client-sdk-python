#!/bin/bash -xv

. ./venv/bin/activate

set -euo pipefail

rm dist/*
./venv/bin/python3 setup.py sdist
./venv/bin/pip install --upgrade twine

export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-AgENdGVzdC5weXBpLm9yZwIkNGVmMTllNDUtMjM1Yi00YTVhLWJkNWYtZDBhYzc5NjZhMmEwAAIleyJwZXJtaXNzaW9ucyI6ICJ1c2VyIiwgInZlcnNpb24iOiAxfQAABiC54pvKHX1RI4wSUk7rWKLw5abBSH0HtWKWBygC1PXaPw"
./venv/bin/python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*


