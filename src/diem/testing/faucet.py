# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Testnet Faucet service client

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

import functools, os

from aiohttp import ClientSession
from diem import diem_types, bcs
from diem.jsonrpc.async_client import AsyncClient, Retry, TransactionExecutionFailed
from diem.testing.local_account import LocalAccount
from diem.testing.constants import FAUCET_URL, XUS
from typing import Optional, Tuple, Union


class Faucet:
    """Faucet service is a proxy server to mint coins for your test account on Testnet

    See https://github.com/diem/diem/blob/master/json-rpc/docs/service_testnet_faucet.md for more details
    """

    def __init__(
        self,
        client: AsyncClient,
        url: Union[str, None] = None,
        retry: Union[Retry, None] = None,
    ) -> None:
        self._client: AsyncClient = client
        self._url: str = url or os.getenv("DIEM_FAUCET_URL") or FAUCET_URL
        self._retry: Retry = retry or Retry(5, 0.2, Exception)

    async def gen_account(self, currency_code: str = XUS, dd_account: bool = False) -> LocalAccount:
        account = LocalAccount.generate()
        await self.mint(account.auth_key.hex(), 100_000_000_000, currency_code, dd_account)
        return account

    async def gen_vasp(self, currency_code: str = XUS, base_url: str = "") -> Tuple[LocalAccount, LocalAccount]:
        """Generates a ParentVASP account with a ChildVASP account"""

        parent = await self.gen_account(currency_code)
        if base_url:
            await parent.reset_dual_attestation(self._client, base_url)
        child, payload = parent.new_child_vasp(0, XUS)
        await parent.apply_txn(self._client, payload)

        return (parent, child)

    async def mint(
        self,
        authkey: str,
        amount: int,
        currency_code: str,
        dd_account: bool = False,
        diem_id_domain: Optional[str] = None,
        is_remove_domain: bool = False,
    ) -> None:
        await self._retry.execute(
            functools.partial(
                self._mint_without_retry,
                authkey,
                amount,
                currency_code,
                dd_account,
                diem_id_domain,
                is_remove_domain,
            )
        )

    async def _mint_without_retry(
        self,
        authkey: str,
        amount: int,
        currency_code: str,
        dd_account: bool = False,
        diem_id_domain: Optional[str] = None,
        is_remove_domain: bool = False,
    ) -> None:
        params = {
            "amount": amount,
            "auth_key": authkey,
            "currency_code": currency_code,
            "return_txns": "true",
            "is_designated_dealer": "true" if dd_account else "false",
            "is_remove_domain": "true" if is_remove_domain else "false",
        }
        if diem_id_domain:
            params["diem_id_domain"] = diem_id_domain
        async with ClientSession(raise_for_status=True) as session:
            async with session.post(self._url, params=params) as response:
                de = bcs.BcsDeserializer(bytes.fromhex(await response.text()))

        for i in range(de.deserialize_len()):
            txn = de.deserialize_any(diem_types.SignedTransaction)
            try:
                await self._client.wait_for_transaction(txn)
            except TransactionExecutionFailed as e:
                if txn.vm_status.explanation.reason == "EDOMAIN_ALREADY_EXISTS":
                    continue
                raise e
