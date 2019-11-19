#!/bin/bash
set -euo pipefail

# C Stuff
rm -rf build
mkdir build
cd build || exit
cmake ..
make VERBOSE=1
cd ..
