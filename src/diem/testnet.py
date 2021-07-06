# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Provides utilities for working with Diem Testnet.

```python

from diem import testnet
from diem.testing import LocalAccount

# create client connects to testnet
client = testnet.create_client()

# create faucet for minting coins for your testing account
faucet = testnet.Faucet(client)

# create a local account and mint some coins for it
account: LocalAccount = faucet.gen_account()

```

"""

import requests
import typing

from . import diem_types, jsonrpc, utils, chain_ids, bcs, identifier, stdlib
from .testing import LocalAccount, DD_ADDRESS


JSON_RPC_URL: str = "https://testnet.diem.com/v1"
FAUCET_URL: str = "https://testnet.diem.com/mint"
CHAIN_ID: diem_types.ChainId = chain_ids.TESTNET

DESIGNATED_DEALER_ADDRESS: diem_types.AccountAddress = utils.account_address(DD_ADDRESS)
TEST_CURRENCY_CODE: str = "XUS"
HRP: str = identifier.TDM


def create_client() -> jsonrpc.Client:
    """create a jsonrpc.Client connects to Testnet public full node cluster"""

    return jsonrpc.Client(JSON_RPC_URL)


def gen_vasp_account(client: jsonrpc.Client, base_url: str) -> LocalAccount:
    raise Exception("deprecated: use `gen_account` instead")


def gen_account(
    client: jsonrpc.Client, dd_account: bool = False, base_url: typing.Optional[str] = None
) -> LocalAccount:
    """generates a Testnet onchain account"""

    account = Faucet(client).gen_account(dd_account=dd_account)
    if base_url:
        payload = stdlib.encode_rotate_dual_attestation_info_script_function(
            new_url=base_url.encode("utf-8"), new_key=account.compliance_public_key_bytes
        )
        apply_txn(client, account, payload)
    return account


def gen_child_vasp(
    client: jsonrpc.Client,
    parent_vasp: LocalAccount,
    initial_balance: int = 10_000_000_000,
    currency: str = TEST_CURRENCY_CODE,
) -> LocalAccount:
    child, payload = parent_vasp.new_child_vasp(initial_balance, currency)
    apply_txn(client, parent_vasp, payload)
    return child


def apply_txn(
    client: jsonrpc.Client, vasp: LocalAccount, payload: diem_types.TransactionPayload
) -> jsonrpc.Transaction:
    seq = client.get_account_sequence(vasp.account_address)
    txn = vasp.create_signed_txn(seq, payload)
    client.submit(txn)
    return client.wait_for_transaction(txn)


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

    def mint(
        self,
        authkey: str,
        amount: int,
        currency_code: str,
        dd_account: bool = False,
        vasp_domain: typing.Optional[str] = None,
        is_remove_domain: bool = False,
    ) -> None:
        self._retry.execute(
            lambda: self._mint_without_retry(authkey, amount, currency_code, dd_account, vasp_domain, is_remove_domain)
        )

    def _mint_without_retry(
        self,
        authkey: str,
        amount: int,
        currency_code: str,
        dd_account: bool = False,
        vasp_domain: typing.Optional[str] = None,
        is_remove_domain: bool = False,
    ) -> None:
        response = self._session.post(
            self._url,
            params={
                "amount": amount,
                "auth_key": authkey,
                "currency_code": currency_code,
                "return_txns": "true",
                "is_designated_dealer": "true" if dd_account else "false",
                "vasp_domain": vasp_domain,
                "is_remove_domain": "true" if is_remove_domain else "false",
            },
        )
        response.raise_for_status()

        de = bcs.BcsDeserializer(bytes.fromhex(response.text))
        length = de.deserialize_len()

        for i in range(length):
            txn = de.deserialize_any(diem_types.SignedTransaction)
            try:
                self._client.wait_for_transaction(txn)
            except jsonrpc.TransactionExecutionFailed as e:
                if e.txn.vm_status.explanation.reason == "EDOMAIN_ALREADY_EXISTS":
                    continue
                raise e
