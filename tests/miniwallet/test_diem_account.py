# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import diem_types
from diem.testing import LocalAccount, create_client, Faucet, XUS
from diem.testing.miniwallet.app import Transaction
from diem.testing.miniwallet.app.diem_account import DiemAccount
import pytest


pytestmark = pytest.mark.asyncio  # pyre-ignore


async def test_no_child_accounts():
    client = create_client()
    faucet = Faucet(client)
    account = await faucet.gen_account()
    da = DiemAccount(account, [], client)
    assert da.hrp == account.hrp
    assert da.account_identifier() == account.account_identifier()

    payee = await faucet.gen_account()
    signed_txn_hex = await da.submit_p2p(gen_txn(payee=payee.account_identifier()), (b"", b""))
    signed_txn = diem_types.SignedTransaction.bcs_deserialize(bytes.fromhex(signed_txn_hex))
    assert signed_txn.raw_txn.sender == account.account_address


async def test_submit_p2p_with_unknown_address():
    client = create_client()
    faucet = Faucet(client)
    account = await faucet.gen_account()
    da = DiemAccount(account, [], client)
    with pytest.raises(ValueError):
        payee = LocalAccount().account_identifier()
        await da.submit_p2p(gen_txn(payee=payee), (b"", b""), by_address=LocalAccount().account_address)


async def test_ensure_account_balance_is_always_enough():
    client = create_client()
    faucet = Faucet(client)
    account = LocalAccount.generate()
    await faucet.mint(account.auth_key.hex(), 1, XUS)
    da = DiemAccount(account, [], client)
    account_data = await client.must_get_account(account.account_address)
    amount = account_data.balances[0].amount + 1
    payee = await faucet.gen_account()
    txn = await da.submit_p2p(gen_txn(payee=payee.account_identifier(), amount=amount), (b"", b""))
    await client.wait_for_transaction(txn)


def gen_txn(payee: str, amount: int = 1) -> Transaction:
    return Transaction(
        id="txn",
        account_id="id",
        currency="XUS",
        amount=amount,
        status=Transaction.Status.pending,
        type=Transaction.Type.sent_payment,
        payee=payee,
    )
