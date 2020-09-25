# libra-client-sdk-python

Python client sdk library for the Libra.


## Packages Overview

> SPEC = specification
> LIP-X = Libra Improvement Protocol

* `jsonrpc`: libra JSON-RPC APIs client. [SPEC](https://github.com/libra/libra/blob/master/json-rpc/json-rpc-spec.md)
- `stdlib`: generated code, move stdlib script utils for constructing transaction script playload.
- `libra_types`: generated code, Libra on-chain data structure types. Mostly generated code with small extension code for attaching handy functions to generated types.
- `utils`: utility functions, account address utils, currency code, hashing, hex encoding / decoding, transaction utils.
- `identifier`: [LIP-5](https://lip.libra.org/lip-5/)
  - `AccountIdentifier`: encoding & decoding Libra Account Identifier.
  - `IntentIdentifier`:  encoding & decoding Libra Intent Identifier.
- `testnet`: Testnet utility, minting coins, create Testnet client, chain id, Testnet JSON-RPC URL.
- `txnmetadata`: utils for creating peer to peer transaction metadata. [LIP-4](https://lip.libra.org/lip-4/)


## Build & Test Pylibra

```
make init
make test
```

run specific test:

```
TEST=<test file / test name> make test
```

## Upgrade to latest libra release

```
cd libra
git pull origin master
```
