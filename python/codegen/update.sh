#!/bin/bash -xv
set -euo pipefail

# generate pypthon code
cargo run ../../libra/testsuite/generate-format/tests/staged/libra.yaml > ../src/pylibra/_lcs/_libra_types.py
