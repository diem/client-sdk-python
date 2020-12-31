# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time, typing
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import (
    identifier,
    jsonrpc,
    diem_types,
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

    compliance_key: typing.Optional[Ed25519PrivateKey]

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

    def add_child_vasp(self) -> jsonrpc.Transaction:
        child_vasp = LocalAccount.generate()
        self._children.append(child_vasp)
        txn = self.create_transaction(
            self._parent_vasp,
            stdlib.encode_create_child_vasp_account_script(
                coin_type=utils.currency_code(testnet.TEST_CURRENCY_CODE),
                child_address=child_vasp.account_address,
                auth_key_prefix=child_vasp.auth_key.prefix(),
                add_all_currencies=False,
                child_initial_balance=2_000_000_000,
            ),
            testnet.TEST_CURRENCY_CODE,
        )

        return self.submit_and_wait(self._parent_vasp.sign(txn))

    def init_compliance_keys(self) -> jsonrpc.Transaction:
        self.compliance_key = Ed25519PrivateKey.generate()
        txn = self.create_transaction(
            self._parent_vasp,
            stdlib.encode_rotate_dual_attestation_info_script(
                new_url=b"http://helloworld.org", new_key=utils.public_key_bytes(self.compliance_key.public_key())
            ),
            testnet.TEST_CURRENCY_CODE,
        )
        return self.submit_and_wait(self._parent_vasp.sign(txn))

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

    def get_sequence_number(self, account: LocalAccount) -> int:
        return self._client.get_account_sequence(account.account_address)

    def available_child_vasp(self) -> LocalAccount:
        return self._children[0]

    def submit_and_wait(
        self,
        txn: typing.Union[diem_types.SignedTransaction, str],
    ) -> jsonrpc.Transaction:
        self._client.submit(txn)
        return self._client.wait_for_transaction(txn)

    def create_transaction(self, sender, script, currency) -> diem_types.RawTransaction:
        sender_account_sequence = self.get_sequence_number(sender)
        return diem_types.RawTransaction(
            sender=sender.account_address,
            sequence_number=sender_account_sequence,
            payload=diem_types.TransactionPayload__Script(script),
            max_gas_amount=1_000_000,
            gas_unit_price=0,
            gas_currency_code=currency,
            expiration_timestamp_secs=int(time.time()) + 30,
            chain_id=self._chain_id,
        )
