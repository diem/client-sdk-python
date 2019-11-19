#!/bin/bash -xv
set -euo pipefail

# Build libra-dev first
cd libra-dev
cargo build
cargo test
cd ..

# Then build rust client
cd rust
cargo build
cd ..
