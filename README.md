# pylibra-beta & pylibra2

Python Client libraries for the Libra network.

## Build & Test

```
cd python
./build.sh
./test.sh
```

## Upgrade to latest libra release

```
cd libra
git fetch
git reset --hard origin/testnet
cd ..

./venv/bin/python3 setup.py vendor
./codegen.sh
./test.sh
```
