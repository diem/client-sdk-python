# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import RestClient, AccountResource, Transaction, AppConfig, RefundReason
from diem import jsonrpc, stdlib, utils, txnmetadata, diem_types, identifier
from typing import Optional
from ..conftest import wait_for_balance, wait_for_event, wait_for_payment_transaction_complete
import pytest


@pytest.mark.parametrize(
    "invalid_metadata",
    [
        b"",
        b"invalid metadata",
        b"9900000000",  # unknown metadata variant
        b"0109000000",  # invalid general metadata version
        b"0209",  # invalid travel rule metadata version
        b"0409",  # invalid refund metadata version
        b"0509",  # invalid coin trade metadata version
    ],
)
def test_receive_payment_with_invalid_metadata(
    stub_client: RestClient,
    target_client: RestClient,
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

    1. Generate a valid account identifier from receiver account as payee.
    2. Submit a p2p transaction with invalid metadata, and wait for it is executed.
    3. Send a valid payment to the valid account identifier.
    4. Assert receiver account received the valid payment.

    """

    amount = 1_000_000
    sender_account = stub_client.create_account(balances={currency: amount})
    receiver_account = target_client.create_account()
    try:
        account_identifier = receiver_account.generate_account_identifier()
        receiver_account_address = identifier.decode_account_address(account_identifier, hrp)
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

        pay = sender_account.send_payment(currency=currency, amount=amount, payee=account_identifier)
        wait_for_payment_transaction_complete(sender_account, pay.id)
        wait_for_balance(receiver_account, currency, amount)
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize("amount", [10_000, 1200_000, 125550_000])
def test_receive_payment_with_general_metadata_and_valid_from_and_to_subaddresses(
    stub_client: RestClient,
    target_client: RestClient,
    currency: str,
    amount: int,
) -> None:
    """
    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Send a payment to the account identifier.
    3. Wait for the transaction executed successfully.
    4. Assert receiver account received the fund.

    """

    sender_account = stub_client.create_account(balances={currency: amount})
    receiver_account = target_client.create_account()
    try:
        payee = receiver_account.generate_account_identifier()
        pay = sender_account.send_payment(currency=currency, amount=amount, payee=payee)
        wait_for_payment_transaction_complete(sender_account, pay.id)
        wait_for_balance(receiver_account, currency, amount)
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize(  # pyre-ignore
    "invalid_to_subaddress", [None, b"", b"bb4a3ba109a3175f", b"subaddress_more_than_8_bytes", b"too_short"]
)
def test_receive_payment_with_general_metadata_and_invalid_to_subaddress(
    stub_client: RestClient,
    target_client: RestClient,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    invalid_to_subaddress: Optional[bytes],
) -> None:
    """When received a payment with general metadata and invalid to subaddress,
    receiver should refund the payment by using RefundMetadata with reason `invalid subaddress`.

    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Create a general metadata with valid from subaddress and invalid to subaddress.
    3. Send payment transaction from sender to receiver on-chain account.
    4. Wait for the transaction executed successfully.
    5. Assert sender account received a payment transaction with refund metadata.
    6. Assert receiver account does not receive funds.

    """

    amount = 1_000_000
    sender_account = stub_client.create_account(balances={currency: amount})
    receiver_account = target_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        receiver_account_address: diem_types.AccountAddress = identifier.decode_account_address(
            receiver_account_identifier, hrp
        )

        sender_account_identifier = sender_account.generate_account_identifier()
        valid_from_subaddress = identifier.decode_account_subaddress(sender_account_identifier, hrp)
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

        wait_for_event(
            sender_account,
            "created_transaction",
            status=Transaction.Status.completed,
            refund_diem_txn_version=original_payment_txn.version,
            refund_reason=RefundReason.invalid_subaddress,
        )
        assert receiver_account.balance(currency) == 0
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize(  # pyre-ignore
    "invalid_from_subaddress", [None, b"", b"bb4a3ba109a3175f", b"subaddress_more_than_8_bytes", b"too_short"]
)
def test_receive_payment_with_general_metadata_and_invalid_from_subaddress(
    stub_client: RestClient,
    target_client: RestClient,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    invalid_from_subaddress: Optional[bytes],
) -> None:
    """When received a payment with general metadata and invalid from subaddress,
    receiver is not required to take any action on it as long as to subaddress is valid.

    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Create a general metadata with invalid from subaddress and valid to subaddress.
    3. Send payment transaction from sender to receiver on-chain account.
    4. Wait for the transaction executed successfully.
    5. Assert receiver account received funds eventually.

    """

    amount = 1_000_000
    sender_account = stub_client.create_account(balances={currency: amount})
    receiver_account = target_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        receiver_account_address = identifier.decode_account_address(receiver_account_identifier, hrp)

        valid_to_subaddress = identifier.decode_account_subaddress(receiver_account_identifier, hrp)
        invalid_metadata = txnmetadata.general_metadata(invalid_from_subaddress, valid_to_subaddress)
        stub_config.account.submit_and_wait_for_txn(
            diem_client,
            stdlib.encode_peer_to_peer_with_metadata_script(
                currency=utils.currency_code(currency),
                amount=amount,
                payee=receiver_account_address,
                metadata=invalid_metadata,
                metadata_signature=b"",
            ),
        )
        wait_for_balance(receiver_account, currency, amount)
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize(
    "invalid_from_subaddress", [None, b"", b"bb4a3ba109a3175f", b"subaddress_more_than_8_bytes", b"too_short"]
)
@pytest.mark.parametrize(  # pyre-ignore
    "invalid_to_subaddress", [None, b"", b"bb4a3ba109a3175f", b"subaddress_more_than_8_bytes", b"too_short"]
)
def test_receive_payment_with_general_metadata_and_invalid_subaddresses(
    stub_client: RestClient,
    target_client: RestClient,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    invalid_to_subaddress: Optional[bytes],
    invalid_from_subaddress: Optional[bytes],
    stub_wallet_pending_income_account: AccountResource,
) -> None:
    """When received a payment with general metadata and invalid subaddresses, it is considered
    same with the case received invalid to subaddress, and receiver should refund the payment.

    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Create a general metadata with invalid from subaddress and invalid to subaddress.
    3. Send payment transaction from sender to receiver on-chain account.
    4. Wait for the transaction executed successfully.
    5. Assert sender account received a payment transaction with refund metadata.
    6. Assert receiver account does not receive funds.

    """

    amount = 1_000_000
    sender_account = stub_client.create_account(balances={currency: amount})
    receiver_account = target_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        receiver_account_address = identifier.decode_account_address(receiver_account_identifier, hrp)

        invalid_metadata = txnmetadata.general_metadata(invalid_from_subaddress, invalid_to_subaddress)
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

        wait_for_event(
            stub_wallet_pending_income_account,
            "created_transaction",
            status=Transaction.Status.completed,
            refund_diem_txn_version=original_payment_txn.version,
            refund_reason=RefundReason.invalid_subaddress,
        )
        assert receiver_account.balance(currency) == 0
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize("invalid_refund_txn_version", [0, 1, 18446744073709551615])
def test_receive_payment_with_refund_metadata_and_invalid_transaction_version(
    stub_client: RestClient,
    target_client: RestClient,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    invalid_refund_txn_version: int,
) -> None:
    """
    When received a payment transaction with invalid refund metadata, it's up to wallet
    application to decide how to handle, this test makes sure the wallet application
    should be able to continue to receive following up valid payment transactions.

    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Submit payment transaction with refund metadata and invalid txn version.
    3. Wait for the transaction executed successfully.
    4. Send a valid payment to the account identifier.
    5. Assert receiver account received the valid payment.

    """

    amount = 120_000
    sender_account = stub_client.create_account(balances={currency: amount})
    receiver_account = target_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        receiver_account_address = identifier.decode_account_address(receiver_account_identifier, hrp)

        reason = diem_types.RefundReason__OtherReason()
        metadata = txnmetadata.refund_metadata(invalid_refund_txn_version, reason)
        stub_config.account.submit_and_wait_for_txn(
            diem_client,
            stdlib.encode_peer_to_peer_with_metadata_script(
                currency=utils.currency_code(currency),
                amount=amount * 2,
                payee=receiver_account_address,
                metadata=metadata,
                metadata_signature=b"",
            ),
        )
        assert receiver_account.balance(currency) == 0

        pay = sender_account.send_payment(currency, amount, payee=receiver_account_identifier)
        wait_for_payment_transaction_complete(sender_account, pay.id)
        wait_for_balance(receiver_account, currency, amount)
    finally:
        receiver_account.log_events()
        sender_account.log_events()
