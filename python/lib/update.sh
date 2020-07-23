#!/bin/bash -xv
set -euo pipefail

rm -rf src || true
ln -s ../../libra ./src

rm data.h || true
cp src/client/libra-dev/include/data.h data.h

rm *.a || true
cargo install cross || true

# hack to make LTO work
sed -i '' -e 's/, \"cdylib\"//' src/client/libra-dev/Cargo.toml
export CARGO_PROFILE_RELEASE_LTO=true
export RUSTFLAGS="-C panic=abort -C debuginfo=0"
cp Cross.toml src/

# build linux release
cd src
cross build -p libra-dev --target x86_64-unknown-linux-gnu --locked --release
cd ..

cp src/target/x86_64-unknown-linux-gnu/release/liblibra_dev.a liblibra_dev-linux-x86_64.a

# build dawrin release
cd src
cross build -p libra-dev --target x86_64-apple-darwin --locked --release
cd ..

cp src/target/x86_64-apple-darwin/release/liblibra_dev.a liblibra_dev-darwin-x86_64.a

# build windows release
cd src
cross build -p libra-dev --target x86_64-pc-windows-gnu --locked --release
cd ..

cp src/target/x86_64-pc-windows-gnu/release/liblibra_dev.a liblibra_dev-windows-x86_64.a

cd src && git reset --hard && cd ..
rm src/Cross.toml
rm -rf src || true
