#!/bin/bash -xv
# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

LIBRA=./libra

# Add transaction builders
(cd "$LIBRA" && cargo build -p transaction-builder-generator)
"$LIBRA/target/debug/generate-transaction-builders"\
    --language python3\
    --module-name stdlib\
    --with-libra-types "$LIBRA/testsuite/generate-format/tests/staged/libra.yaml"\
    --serde-package-name pylibra\
    --libra-package-name pylibra\
    --target-source-dir src/pylibra\
    "$LIBRA/language/stdlib/compiled/transaction_scripts/abi"

# Formatting
. ./venv/bin/activate
./venv/bin/pip3 install --upgrade black
./venv/bin/python3 -m black src/pylibra/*_types/__init__.py src/pylibra/lcs/__init__.py src/pylibra/stdlib/__init__.py
