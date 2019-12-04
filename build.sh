#!/bin/bash -xv
set -euo pipefail

# Create C to Rust bindings
bindgen libra-dev/include/data.h \
  --with-derive-default --with-derive-eq --use-array-pointers-in-arguments --default-enum-style=rust \
  --whitelist-type=LibraStatus \
  --whitelist-type=LibraEventHandle --whitelist-type=LibraAccountResource \
  --whitelist-type=LibraP2PTransferTransactionArgument --whitelist-type=LibraTransactionPayload --whitelist-type=LibraRawTransaction --whitelist-type=LibraSignedTransaction \
  --whitelist-type=TransactionType \
  -o libra-dev/src/data.rs

# Build libra-dev first
cd libra-dev
cargo build
cargo clippy -- -A clippy::missing-safety-doc -D warnings
cargo fmt --all -- --check
cargo test
cd ..

# Then build rust client
cd rust
cargo build
cd ..
