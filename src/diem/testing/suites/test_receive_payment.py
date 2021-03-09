# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import RestClient, AccountResource, Transaction, AppConfig, RefundReason
from diem import jsonrpc, stdlib, utils, txnmetadata, diem_types
from typing import Generator, Optional
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


@pytest.mark.parametrize("invalid_metadata", [b"", b"invalid metadata"])
def test_receive_payment_with_invalid_metadata(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    invalid_metadata: bytes,
) -> None:
    """When received a payment with invalid metadata, it is up to the wallet application how to handle it.
    This test makes sure target wallet application should continue to process valid transactions after
    received such an on-chain transaction.

    Test Plan:
    1. Generate a valid payment URI from receiver account.
    2. Submit a p2p transaction with invalid metadata, and wait for it is executed.
    3. Send a valid payment to the payment URI.
    4. Assert receiver account received the valid payment.
    """

    uri = receiver_account.generate_payment_uri()
    receiver_account_address = uri.intent(hrp).account_address
    stub_config.account.submit_and_wait_for_txn(
        diem_client,
        stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(currency),
            amount=amount * 2,
            payee=receiver_account_address,
            metadata=invalid_metadata,
            metadata_signature=b"",
        ),
    )
    assert receiver_account.balance(currency) == 0

    pay = sender_account.send_payment(currency=currency, amount=amount, payee=uri.intent(hrp).account_id)
    wait_for_payment_transaction_complete(sender_account, pay.id)
    receiver_account.wait_for_balance(currency, amount)


def test_receive_payment_with_general_metadata_and_valid_from_and_to_subaddresses(
    sender_account: AccountResource, receiver_account: AccountResource, currency: str, hrp: str
) -> None:
    """
    Test Plan:
    1. Generate a valid payment URI from receiver account.
    2. Send a payment to the payee from the valid payment URI.
    4. Wait for the transaction executed successfully.
    5. Assert receiver account received the fund.
    """
    uri = receiver_account.generate_payment_uri()
    pay = sender_account.send_payment(currency=currency, amount=amount, payee=uri.intent(hrp).account_id)
    wait_for_payment_transaction_complete(sender_account, pay.id)
    receiver_account.wait_for_balance(currency, amount)


@pytest.mark.parametrize(  # pyre-ignore
    "invalid_to_subaddress", [None, b"", b"bb4a3ba109a3175f", b"subaddress_more_than_8_bytes", b"too_short"]
)
def test_receive_payment_with_general_metadata_and_invalid_to_subaddress(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    invalid_to_subaddress: Optional[bytes],
) -> None:
    """When received a payment with general metadata and invalid to subaddress,
    receiver should refund the payment by using RefundMetadata with reason `invalid subaddress`.

    Test Plan:
    1. Generate a valid payment URI from the receiver account.
    2. Create a general metadata with valid from subaddress and invalid to subaddress.
    3. Send payment transaction from sender to receiver on-chain account.
    4. Wait for the transaction executed successfully.
    5. Assert sender account received a payment transaction with refund metadata.
    6. Assert receiver account does not receive funds.
    """

    receiver_uri = receiver_account.generate_payment_uri()
    receiver_account_address: diem_types.AccountAddress = receiver_uri.intent(hrp).account_address

    sender_uri = sender_account.generate_payment_uri()
    valid_from_subaddress = sender_uri.intent(hrp).subaddress
    invalid_metadata = txnmetadata.general_metadata(valid_from_subaddress, invalid_to_subaddress)
    original_payment_txn: jsonrpc.Transaction = stub_config.account.submit_and_wait_for_txn(
        diem_client,
        stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(currency),
            amount=amount,
            payee=receiver_account_address,
            metadata=invalid_metadata,
            metadata_signature=b"",
        ),
    )

    sender_account.wait_for_event(
        "created_transaction",
        status=Transaction.Status.completed,
        refund_diem_txn_version=original_payment_txn.version,
        refund_reason=RefundReason.invalid_subaddress,
    )
    assert receiver_account.balance(currency) == 0


def wait_for_payment_transaction_complete(account: AccountResource, payment_id: str) -> None:
    # MiniWallet stub generates `updated_transaction` event when transaction is completed on-chain
    # Payment id is same with Transaction id.
    account.wait_for_event("updated_transaction", status=Transaction.Status.completed, id=payment_id)
