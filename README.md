# libra-client-dev

Client libraries for the Libra network.

# Build & Test Pylibra

```
cd python
./build.sh
./test.sh
```

# Upgrade to latest libra release

```
cd libra
git fetch
git reset --hard origin/testnet
cd ..

cd python
./venv/bin/python3 setup.py vendor
./codegen.sh
./test.sh
```
