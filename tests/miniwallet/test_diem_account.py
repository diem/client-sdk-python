# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import testnet, diem_types
from diem.testing import LocalAccount
from diem.testing.miniwallet.app import Transaction
from diem.testing.miniwallet.app.diem_account import DiemAccount
import pytest


def test_no_child_accounts():
    client = testnet.create_client()
    account = testnet.gen_account(client)
    da = DiemAccount(account, [], client)
    assert da.hrp == account.hrp
    assert da.account_identifier(None) == account.account_identifier(None)

    signed_txn_hex = da.submit_p2p(gen_txn(), (b"", b""))
    signed_txn = diem_types.SignedTransaction.bcs_deserialize(bytes.fromhex(signed_txn_hex))
    assert signed_txn.raw_txn.sender == account.account_address


def test_submit_p2p_with_unknown_address():
    client = testnet.create_client()
    account = testnet.gen_account(client)
    da = DiemAccount(account, [], client)
    with pytest.raises(ValueError):
        da.submit_p2p(gen_txn(), (b"", b""), by_address=LocalAccount().account_address)


def gen_txn() -> Transaction:
    return Transaction(
        id="txn",
        account_id="id",
        currency="XUS",
        amount=1,
        status=Transaction.Status.pending,
        type=Transaction.Type.sent_payment,
        payee=LocalAccount().account_identifier(None),
    )
