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

# C Stuff
rm -rf build
mkdir build
cd build
cmake ..
make VERBOSE=1

# Test!
cd rust && ./test.sh && cd ..
./c/c-client
./cpp/cpp-client