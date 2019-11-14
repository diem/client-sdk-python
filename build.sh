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
cargo test
cd ..

# C Stuff
rm -rf build
mkdir build
cd build
cmake ..
make VERBOSE=1

# Test!
./c/c-client
./cpp/cpp-client