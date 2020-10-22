# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Provides utilities for working with Libra Testnet.

```python

from libra import testnet, LocalAccount

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

from . import libra_types, jsonrpc, utils, local_account, serde_types, auth_key


JSON_RPC_URL = "https://testnet.libra.org/v1"
FAUCET_URL = "https://testnet.libra.org/mint"
CHAIN_ID = libra_types.ChainId(value=serde_types.uint8(2))  # pyre-ignore

DESIGNATED_DEALER_ADDRESS: libra_types.AccountAddress = utils.account_address("000000000000000000000000000000dd")
TEST_CURRENCY_CODE: str = "Coin1"


def create_client() -> jsonrpc.Client:
    """create a jsonrpc.Client connects to Testnet public full node cluster"""

    return jsonrpc.Client(JSON_RPC_URL)


class Faucet:
    """Faucet service is a proxy server to mint coins for your test account on Testnet

    See https://github.com/libra/libra/blob/master/json-rpc/docs/service_testnet_faucet.md for more details
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

    def gen_account(self, currency_code: str = TEST_CURRENCY_CODE) -> local_account.LocalAccount:
        account = local_account.LocalAccount.generate()

        self.mint(account.auth_key.hex(), 5_000_000_000, currency_code)

        return account

    def mint(self, authkey: str, amount: int, currency_code: str) -> None:
        self._retry.execute(lambda: self._mint_with_validation(authkey, amount, currency_code))

    def _mint_with_validation(self, authkey: str, amount: int, currency_code: str) -> None:
        seq = self._retry.execute(lambda: self._mint_without_retry(authkey, amount, currency_code))
        self._retry.execute(lambda: self._wait_for_account_seq(seq))
        self._validate_mint_result(authkey, amount, currency_code)

    def _validate_mint_result(self, authkey: str, amount: int, currency_code: str) -> None:
        account_address = auth_key.AuthKey(bytes.fromhex(authkey)).account_address()
        account = self._client.get_account(account_address)
        if account is not None:
            balance = next(iter([b for b in account.balances if b.currency == currency_code]), None)

        if balance is None or balance.amount < amount:
            raise Exception("mint failed, please retry")

    def _wait_for_account_seq(self, seq: int) -> None:
        seq_num = self._client.get_account_sequence(DESIGNATED_DEALER_ADDRESS)
        if seq_num < seq:
            raise Exception(f"sequence number {seq_num} < {seq}")

    def _mint_without_retry(self, authkey: str, amount: int, currency_code: str) -> int:
        response = self._session.post(
            FAUCET_URL,
            params={
                "amount": amount,
                "auth_key": authkey,
                "currency_code": currency_code,
            },
        )
        response.raise_for_status()
        return int(response.text)
