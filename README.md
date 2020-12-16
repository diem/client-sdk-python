# The official Diem Client SDK for Python.

[Documentation](https://developers.diem.com/docs/python-client-sdk-docs)

## Modules Overview

> SPEC = specification

> DIP-X = Diem Improvement Protocol

Root module name: `diem`

Sub-modules:

- `jsonrpc`: diem JSON-RPC APIs client and API response types. [SPEC](https://github.com/diem/diem/blob/master/json-rpc/json-rpc-spec.md)
- `stdlib`: generated code, move stdlib script utils for constructing transaction script playload.
- `diem_types`: generated code, Diem on-chain data structure types for encoding and decoding [BCS](https://crates.io/crates/bcs) data.
- `utils`: utility functions, account address utils, currency code, hashing, hex encoding / decoding, transaction utils.
- `AuthKey` | `auth_key`: auth key utils
- `identifier`: Diem Account Identifier and Diem Intent Identifier. [DIP-5](https://dip.diem.com/dip-5/)
- `txnmetadata`: utils for creating peer to peer transaction metadata. [DIP-4](https://dip.diem.com/dip-4/)
- `testnet`: Testnet utility, minting coins, create Testnet client, chain id, Testnet JSON-RPC URL.
- `LocalAccount` | `local_account`: utility for managing local account keys, generate random local account.
- `chain_ids`: list of static chain ids

## Examples

```python3

>>> from diem import jsonrpc, testnet
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
pip install diem-client-sdk
```

## Bugs/Requests

Please use the [GitHub issue tracker](https://github.com/diem/client-sdk-python/issues) to submit bugs or request features.

## Build & Test

```
make init
make test
```

run specific test:

```
TEST=<test file / test name> make test
```
