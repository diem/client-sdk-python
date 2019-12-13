#!/bin/bash -xv
set -euo pipefail

rm -rf src || true
ln -s ../../libra-dev ./src

rm data.h || true
cp src/include/data.h data.h

rm *.a || true
cargo install cross || true

# build linux release
cd src
cross build --target x86_64-unknown-linux-gnu --locked --release
cd ..

cp src/target/x86_64-unknown-linux-gnu/release/liblibra_dev.a liblibra_dev-linux-x86_64.a

# build dawrin release
cd src
cross build --target x86_64-apple-darwin --locked --release
cd ..

cp src/target/x86_64-apple-darwin/release/liblibra_dev.a liblibra_dev-darwin-x86_64.a

rm -rf src || true
