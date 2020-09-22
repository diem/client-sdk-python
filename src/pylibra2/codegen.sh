#!/bin/bash -xv

set -euo pipefail

export http_proxy=fwdproxy:8080
export https_proxy=fwdproxy:8080

LIBRA=/tmp/libra

rm -rf $LIBRA || true
git clone -b testnet --depth 1 https://github.com/libra/libra $LIBRA
SRC_DIR=`pwd`

# Add transaction builders
(cd "$LIBRA" && git reset --hard testnet && cargo run -p transaction-builder-generator -- \
    --language python3\
    --module-name stdlib\
    --with-libra-types "$LIBRA/testsuite/generate-format/tests/staged/libra.yaml"\
    --serde-package-name ".." \
    --libra-package-name ".." \
    --target-source-dir "$SRC_DIR" \
    "$LIBRA/language/stdlib/compiled/transaction_scripts/abi"
)
