# The official Libra Client SDK for Python.


## Modules Overview

> SPEC = specification

> LIP-X = Libra Improvement Protocol

Root module name: `libra`

Sub-modules:

- `jsonrpc`: libra JSON-RPC APIs client and API response types. [SPEC](https://github.com/libra/libra/blob/master/json-rpc/json-rpc-spec.md)
- `stdlib`: generated code, move stdlib script utils for constructing transaction script playload.
- `libra_types`: generated code, Libra on-chain data structure types for encoding and decoding [LCS](https://libra.github.io/libra/libra_canonical_serialization/index.html) data.
- `utils`: utility functions, account address utils, currency code, hashing, hex encoding / decoding, transaction utils.
- `AuthKey` | `auth_key`: auth key utils
- `identifier`: Libra Account Identifier and Libra Intent Identifier. [LIP-5](https://lip.libra.org/lip-5/)
- `txnmetadata`: utils for creating peer to peer transaction metadata. [LIP-4](https://lip.libra.org/lip-4/)
- `testnet`: Testnet utility, minting coins, create Testnet client, chain id, Testnet JSON-RPC URL.
- `LocalAccount` | `local_account`: utility for managing local account keys, generate random local account.

## Examples

```python3

>>> from libra import jsonrpc, testnet
>>> client = jsonrpc.Client(testnet.JSON_RPC_URL)
>>> client.get_metadata()
version: 3300304
timestamp: 1601492912847973
chain_id: 2

```

You can find more examples under the [`examples`](./examples/) directory:

* [Create Child VASP account](./examples/create_child_vasp.py)
* [All Types Peer To Peer Transfer](./examples/p2p_transfer.py)
* [Intent Identifier](./examples/intent_identifier.py)
* [Refund](./examples/refund.py)

Note: `make test` runs all examples too, see the Makefile for details.

## Download

```
pip install libra-client-sdk
```

## Documentation

After installing the package:

```bash
python -m pydoc libra
```

## Bugs/Requests

Please use the [GitHub issue tracker](https://github.com/libra/libra-client-sdk-python/issues) to submit bugs or request features.

## Build & Test

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

## Release a new version

* Update setup.py, bump up version
* Commit and merge

```
git checkout <releasse version>
make tagrelease
git push origin --tags
```
