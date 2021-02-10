#!/usr/bin/env python3

import sys, getopt
from wallet import WalletApp
from diem import testnet

opts, _ = getopt.getopt(sys.argv[1:], "p:")

client = testnet.create_client()
print(f"generating sample VASP account on testnet")
app = WalletApp.generate(f"sample wallet app", client)

for option, value in opts:
    if option == "-p":
        app.offchain_service_port = int(value)

print(f"Parent VASP account: {app.parent_vasp.account_address.to_hex()}")
print(f"Child VASP accounts: {list(map(lambda a: a.account_address.to_hex(), app.child_vasps))}")
print(f"chain id: {client.get_last_known_state().chain_id}")
print(f"hrp: {app.hrp}")

print(f"starting http server")
server = app.start_server()
print(f"started at port: {app.offchain_service_port}")
server.serve_forever()
