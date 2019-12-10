#!/bin/bash
set -euo pipefail

rm -rf src || true
mkdir src
cd src
tar zxvf ../libra-dev.tar.gz
cd ..

cargo build --locked --release --manifest-path ./src/Cargo.toml --target-dir ./target
