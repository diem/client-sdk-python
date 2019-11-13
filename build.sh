#!/bin/bash -xv
set -euo pipefail

# Build libra-dev first
cd libra-dev
cargo test
cargo build
cd ..

# Then build everything else
rm -rf build
mkdir build
cd build
cmake ..
make VERBOSE=1

# Test!
./c/c-client
./cpp/cpp-client