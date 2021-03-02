[![pypi](https://img.shields.io/pypi/v/diem)](https://pypi.org/project/diem/)
![Apache V2 License](https://img.shields.io/pypi/l/diem)
![Python versoins](https://img.shields.io/pypi/pyversions/diem)

[Documentation](diem/index.html)


[Mini-Wallet API Specification](mini-wallet-api-spec.html)


## Example

```python

>>> from diem import jsonrpc, testnet
>>> client = jsonrpc.Client(testnet.JSON_RPC_URL)
>>> client.get_metadata()
version: 3300304
timestamp: 1601492912847973
chain_id: 2

```

[More examples](examples/index.html)
