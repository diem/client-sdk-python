# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time, secrets, typing
from libra import (
    identifier,
    jsonrpc,
    libra_types,
    stdlib,
    testnet,
    utils,
    LocalAccount,
)


class CustodialApp:
    """CustodialApp is a stub for simulating custodial application on testnet"""

    @staticmethod
    def create(vasp: LocalAccount) -> "CustodialApp":
        c = CustodialApp(vasp)
        c.add_child_vasp()
        c.add_user()
        return c


    _parent_vasp: LocalAccount
    _client: jsonrpc.Client
    _children: typing.List[LocalAccount]
    _users: typing.List[str]

    def __init__(
            self,
            parent_vasp: LocalAccount,
    ) -> None:
        self._parent_vasp = parent_vasp
        # a custodial application runs with its own client
        self._client = testnet.create_client()
        self._chain_id = testnet.CHAIN_ID
        self._children = []
        self._users = []

    def add_child_vasp(self):
        child_vasp = LocalAccount.generate()
        txn = self.create_transaction(
            self._parent_vasp,
            self.get_sequence_number(self._parent_vasp),
            stdlib.encode_create_child_vasp_account_script(
                coin_type=utils.currency_code("LBR"),
                child_address=child_vasp.account_address,
                auth_key_prefix=child_vasp.auth_key.prefix(),
                add_all_currencies=False,
                child_initial_balance=1_000_000,
            )
        )

        self.submit_and_wait(self._parent_vasp.sign(txn))
        self._children.append(child_vasp)

    def add_user(self):
        self._users.append(secrets.token_hex(identifier.LIBRA_SUBADDRESS_SIZE))

    def user_sub_address(self, index: int) -> bytes:
        return utils.sub_address(self.users[index])

    def payment(self, user_id: int, amount: int) -> str:
        account_id = identifier.encode_account(
            utils.account_address_hex(self._children[0].account_address),
            self._users[user_id],
            identifier.TLB  # testnet HRP
        )
        return identifier.encode_intent(account_id, "LBR", amount)

    def submit_and_wait(
        self,
        txn: typing.Union[libra_types.SignedTransaction, str],
    ) -> jsonrpc.Transaction:
        self._client.submit(txn)
        return self._client.wait_for_transaction(txn)

    def get_sequence_number(self, account: LocalAccount) -> int:
        return self._client.get_account_sequence(account.account_address)

    def create_transaction(self, sender, sender_account_sequence, script, currency="LBR"):
        return libra_types.RawTransaction(
            sender=sender.account_address,
            sequence_number=sender_account_sequence,
            payload=libra_types.TransactionPayload__Script(script),
            max_gas_amount=1_000_000,
            gas_unit_price=0,
            gas_currency_code=currency,
            expiration_timestamp_secs=int(time.time()) + 30,
            chain_id=self._chain_id,
        )
