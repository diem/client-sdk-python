#!/bin/bash -xv
set -euo pipefail

# Create C to Rust bindings
bindgen libra-dev/include/data.h \
  --with-derive-default --with-derive-eq --use-array-pointers-in-arguments --default-enum-style=rust \
  --whitelist-type=LibraStatus \
  --whitelist-type=LibraEventHandle --whitelist-type=LibraAccountResource \
  --whitelist-type=LibraP2PTransferTransactionArgument --whitelist-type=LibraTransactionPayload --whitelist-type=LibraRawTransaction --whitelist-type=LibraSignedTransaction \
  --whitelist-type=TransactionType \
  --whitelist-type=LibraAccountKey \
  --whitelist-type=LibraEvent --whitelist-type=LibraPaymentEvent --whitelist-type=LibraEventType \
  -o libra-dev/src/data.rs

# Build libra-dev first
cd libra-dev
cargo build --locked
#cargo clippy -- -A clippy::missing-safety-doc -D warnings   // Disabled due to clippy type mismatch between libra/libra and this repo. Will add it back once we merge back in tree
cargo fmt --all -- --check
cargo test
cd ..
