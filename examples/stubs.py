# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import typing
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import (
    identifier,
    jsonrpc,
    stdlib,
    testnet,
    utils,
    LocalAccount,
)


class CustodialApp:
    """CustodialApp is a stub for simulating custodial application on testnet"""

    @staticmethod
    def create(vasp: LocalAccount, client: jsonrpc.Client) -> "CustodialApp":
        c = CustodialApp(vasp, client)
        c.add_child_vasp()
        c.add_user()
        return c

    _parent_vasp: LocalAccount
    _client: jsonrpc.Client
    _children: typing.List[LocalAccount]
    _users: typing.List[bytes]

    def __init__(
        self,
        parent_vasp: LocalAccount,
        client: jsonrpc.Client,
    ) -> None:
        self._parent_vasp = parent_vasp
        self._client = client
        self._chain_id = testnet.CHAIN_ID
        self._children = []
        self._users = []

    @property
    def compliance_key(self) -> Ed25519PrivateKey:
        return self._parent_vasp.compliance_key

    def add_child_vasp(self) -> jsonrpc.Transaction:
        child_vasp = LocalAccount.generate()
        self._children.append(child_vasp)
        return self._parent_vasp.submit_and_wait_for_txn(
            self._client,
            stdlib.encode_create_child_vasp_account_script(
                coin_type=utils.currency_code(testnet.TEST_CURRENCY_CODE),
                child_address=child_vasp.account_address,
                auth_key_prefix=child_vasp.auth_key.prefix(),
                add_all_currencies=False,
                child_initial_balance=2_000_000_000,
            ),
        )

    def init_compliance_keys(self) -> jsonrpc.Transaction:
        return self._parent_vasp.rotate_dual_attestation_info(self._client, "http://helloworld.org")

    def add_user(self):
        self._users.append(identifier.gen_subaddress())

    def payment(self, user_id: int, amount: int) -> str:
        account_id = identifier.encode_account(
            self._children[0].account_address, self._users[user_id], identifier.TDM  # testnet HRP
        )
        return identifier.encode_intent(account_id, testnet.TEST_CURRENCY_CODE, amount)

    # TODO: change to generate sub address for user when needed
    def find_user_sub_address_by_id(self, user_id: int) -> bytes:
        return self._users[user_id]

    def available_child_vasp(self) -> LocalAccount:
        return self._children[0]
