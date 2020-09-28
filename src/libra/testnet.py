# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import requests
import typing

from . import libra_types, jsonrpc, utils, local_account


JSON_RPC_URL = "https://testnet.libra.org/v1"
FAUCET_URL = "https://testnet.libra.org/mint"
CHAIN_ID = libra_types.ChainId(value=2)  # pyre-ignore

DESIGNATED_DEALER_ADDRESS: libra_types.AccountAddress = utils.account_address("000000000000000000000000000000dd")


def create_client() -> jsonrpc.Client:
    return jsonrpc.Client(JSON_RPC_URL)


class Faucet:
    def __init__(
        self,
        client: jsonrpc.Client,
        url: typing.Union[str, None] = None,
        retry: typing.Union[jsonrpc.Retry, None] = None,
    ):
        self._client = client
        self._url = url or FAUCET_URL
        self._retry = retry or jsonrpc.Retry(5, 0.2, Exception)

    def gen_account(self) -> local_account.LocalAccount:
        account = local_account.LocalAccount.generate()

        self.mint(account.auth_key.hex(), 1_000_000_000, "LBR")

        return account

    def mint(self, *args, **kwargs):
        seq = self._retry.execute(lambda: self._mint_without_retry(*args, **kwargs))
        self._retry.execute(lambda: self._wait_for_account_seq(seq))

    def _wait_for_account_seq(self, seq: int):
        account = self._client.get_account(DESIGNATED_DEALER_ADDRESS)
        if account.sequence_number < seq:
            raise Exception(f"sequence number {account.sequence_number} < {seq}")

    def _mint_without_retry(self, authkey: str, amount: int, currency_code: str) -> int:
        session = requests.Session()
        response = session.post(
            FAUCET_URL,
            params={
                "amount": amount,
                "auth_key": authkey,
                "currency_code": currency_code,
            },
        )
        response.raise_for_status()
        return int(response.text)