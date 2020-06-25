#!/bin/bash -xv
set -euo pipefail

# Generate python code for Libra types and LCS runtime
cargo install serde-generate --version 0.4.0

LIBRA=../libra

$HOME/.cargo/bin/serdegen\
    --language python3\
    --module-name libra_types\
    --with-runtimes serde lcs\
    --serde-package-name pylibra\
    --target-source-dir src/pylibra\
    "$LIBRA/testsuite/generate-format/tests/staged/libra.yaml"

# Add transaction builders
(cd "$LIBRA" && cargo build -p transaction-builder-generator)
"$LIBRA/target/debug/transaction-builder-generator"\
    --language python3\
    --module-name stdlib\
    --serde-package-name pylibra\
    --libra-package-name pylibra\
    --target-source-dir src/pylibra\
    "$LIBRA/language/stdlib/compiled/transaction_scripts/abi"

# Formatting
. ./venv/bin/activate
./venv/bin/pip3 install --upgrade black
./venv/bin/python3 -m black src/pylibra/*_types/__init__.py src/pylibra/lcs/__init__.py src/pylibra/stdlib/__init__.py
