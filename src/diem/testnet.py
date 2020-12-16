# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Provides utilities for working with Diem Testnet.

```python

from diem import testnet, LocalAccount

# create client connects to testnet
client = testnet.create_client()

# create faucet for minting coins for your testing account
faucet = testnet.Faucet(client)

# create a local account and mint some coins for it
account: LocalAccount = faucet.gen_account()

```

"""

import requests
import typing, time

from . import diem_types, jsonrpc, utils, chain_ids, bcs, stdlib, LocalAccount


JSON_RPC_URL: str = "http://testnet.diem.com/v1"
FAUCET_URL: str = "http://testnet.diem.com/mint"
CHAIN_ID: diem_types.ChainId = chain_ids.TESTNET

DESIGNATED_DEALER_ADDRESS: diem_types.AccountAddress = utils.account_address("000000000000000000000000000000dd")
TEST_CURRENCY_CODE: str = "XUS"


def create_client() -> jsonrpc.Client:
    """create a jsonrpc.Client connects to Testnet public full node cluster"""

    return jsonrpc.Client(JSON_RPC_URL)


def gen_vasp_account(client: jsonrpc.Client, base_url: str) -> LocalAccount:
    account = gen_account(client)
    exec_txn(
        client,
        account,
        stdlib.encode_rotate_dual_attestation_info_script(
            new_url=base_url.encode("utf-8"), new_key=account.compliance_public_key_bytes
        ),
    )
    return account


def gen_account(client: jsonrpc.Client, dd_account: bool = False) -> LocalAccount:
    """generates a Testnet onchain account"""

    return Faucet(client).gen_account(dd_account=dd_account)


def gen_child_vasp(
    client: jsonrpc.Client,
    parent_vasp: LocalAccount,
    initial_balance: int = 10_000_000_000,
    currency: str = TEST_CURRENCY_CODE,
) -> LocalAccount:
    child_vasp = LocalAccount.generate()
    exec_txn(
        client,
        parent_vasp,
        stdlib.encode_create_child_vasp_account_script(
            coin_type=utils.currency_code(currency),
            child_address=child_vasp.account_address,
            auth_key_prefix=child_vasp.auth_key.prefix(),
            add_all_currencies=False,
            child_initial_balance=initial_balance,
        ),
    )
    return child_vasp


def exec_txn(client: jsonrpc.Client, sender: LocalAccount, script: diem_types.Script) -> jsonrpc.Transaction:
    """create, submit and wait for the transaction"""

    sender_account_sequence = client.get_account_sequence(sender.account_address)
    expire = 30
    txn = sender.sign(
        diem_types.RawTransaction(  # pyre-ignore
            sender=sender.account_address,
            sequence_number=diem_types.st.uint64(sender_account_sequence),
            payload=diem_types.TransactionPayload__Script(value=script),
            max_gas_amount=1_000_000,
            gas_unit_price=0,
            gas_currency_code=TEST_CURRENCY_CODE,
            expiration_timestamp_secs=int(time.time()) + expire,
            chain_id=CHAIN_ID,
        )
    )
    client.submit(txn)
    return client.wait_for_transaction(txn, timeout_secs=expire)


class Faucet:
    """Faucet service is a proxy server to mint coins for your test account on Testnet

    See https://github.com/diem/diem/blob/master/json-rpc/docs/service_testnet_faucet.md for more details
    """

    def __init__(
        self,
        client: jsonrpc.Client,
        url: typing.Union[str, None] = None,
        retry: typing.Union[jsonrpc.Retry, None] = None,
    ) -> None:
        self._client: jsonrpc.Client = client
        self._url: str = url or FAUCET_URL
        self._retry: jsonrpc.Retry = retry or jsonrpc.Retry(5, 0.2, Exception)
        self._session: requests.Session = requests.Session()

    def gen_account(self, currency_code: str = TEST_CURRENCY_CODE, dd_account: bool = False) -> LocalAccount:
        account = LocalAccount.generate()
        self.mint(account.auth_key.hex(), 100_000_000_000, currency_code, dd_account)
        return account

    def mint(self, authkey: str, amount: int, currency_code: str, dd_account: bool = False) -> None:
        self._retry.execute(lambda: self._mint_without_retry(authkey, amount, currency_code, dd_account))

    def _mint_without_retry(self, authkey: str, amount: int, currency_code: str, dd_account: bool = False) -> None:
        response = self._session.post(
            FAUCET_URL,
            params={
                "amount": amount,
                "auth_key": authkey,
                "currency_code": currency_code,
                "return_txns": "true",
                "is_designated_dealer": "true" if dd_account else "false",
            },
        )
        response.raise_for_status()

        de = bcs.BcsDeserializer(bytes.fromhex(response.text))
        length = de.deserialize_len()

        for i in range(length):
            txn = de.deserialize_any(diem_types.SignedTransaction)
            self._client.wait_for_transaction(txn)
