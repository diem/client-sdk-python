#!/bin/bash -xv
set -euo pipefail

# Generate python code for Libra types and LCS runtime
cargo install serde-generate --version 0.2.1

$HOME/.cargo/bin/serdegen\
    --language python3\
    --name libra_types\
    --with-runtimes serde lcs\
    --target-source-dir src/pylibra\
    ../libra/testsuite/generate-format/tests/staged/libra.yaml

# Fix import of serde_types
sed -i '' -e 's/^import serde_types/from .. import serde_types/g' src/pylibra/libra_types/__init__.py src/pylibra/lcs/__init__.py

# Formatting
. ./venv/bin/activate
./venv/bin/pip3 install --upgrade black
./venv/bin/python3 -m black src/pylibra/*_types/__init__.py src/pylibra/lcs/__init__.py
