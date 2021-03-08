# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import RestClient, AccountResource, Transaction
from diem import identifier
from typing import Generator
import pytest


amount: int = 123


@pytest.fixture
def sender_account(
    stub_client: RestClient, currency: str, pending_income_account: AccountResource
) -> Generator[AccountResource, None, None]:
    account = stub_client.create_account(balances={currency: amount})
    yield account
    account.log_events()
    # MiniWallet stub saves the payment without account information (subaddress / reference id)
    # into a pending income account before process it.
    # Here we log events of the account for showing more context related to the test
    # when test failed.
    pending_income_account.log_events()


@pytest.fixture
def receiver_account(target_client: RestClient) -> Generator[AccountResource, None, None]:
    account = target_client.create_account()
    yield account
    account.log_events()


def test_receive_payment_with_general_metadata_and_unknown_to_subaddress(
    sender_account: AccountResource, receiver_account: AccountResource, currency: str, hrp: str
) -> None:
    """When received a payment with unknown subaddress, receiver should refund the payment
    by using RefundMetadata with reason `invalid subaddress`.

    Test Plan:
    1. Generate a valid payment URI from receiver account.
    2. Create an invalid payee account identifier by the valid account address and an invalid subaddress.
    3. Send a payment to the invalid payee.
    4. Wait for payment completed.
    5. Assert receiver account does not receive fund.
    6. Assert sender account balances will has same balances before send the payment eventually.
    """

    uri = receiver_account.generate_payment_uri()
    receiver_account_address = uri.intent(hrp).account_address
    invalid_subaddress = identifier.gen_subaddress()
    invalid_payee = identifier.encode_account(receiver_account_address, invalid_subaddress, hrp)
    payment = sender_account.send_payment(currency=currency, amount=amount, payee=invalid_payee)
    wait_for_payment_transaction_complete(sender_account, payment.id)
    assert receiver_account.balance(currency) == 0
    sender_account.wait_for_balance(currency, amount)


def wait_for_payment_transaction_complete(account: AccountResource, payment_id: str) -> None:
    # MiniWallet stub generates `updated_transaction` event when transaction is completed on-chain
    # Payment id is same with Transaction id.
    account.wait_for_event("updated_transaction", status=Transaction.Status.completed, id=payment_id)
