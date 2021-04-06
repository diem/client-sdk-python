# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import RestClient, AccountResource, Transaction, AppConfig, RefundReason
from diem import offchain, jsonrpc, stdlib, utils, txnmetadata, diem_types
from typing import Generator, Optional, List
import pytest, json


amount: int = 12345


@pytest.fixture
def sender_account(
    stub_client: RestClient, currency: str, pending_income_account: AccountResource, travel_rule_threshold: int
) -> Generator[AccountResource, None, None]:
    account = stub_client.create_account(balances={currency: travel_rule_threshold})
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


@pytest.mark.parametrize("amount", [1, 123456, 125555])
def test_receive_payment_with_general_metadata_and_valid_from_and_to_subaddresses(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    currency: str,
    hrp: str,
    amount: int,
) -> None:
    """
    Test Plan:

    1. Generate a valid payment URI from receiver account.
    2. Send a payment to the payee from the valid payment URI.
    3. Wait for the transaction executed successfully.
    4. Assert receiver account received the fund.

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


@pytest.mark.parametrize(  # pyre-ignore
    "invalid_from_subaddress", [None, b"", b"bb4a3ba109a3175f", b"subaddress_more_than_8_bytes", b"too_short"]
)
def test_receive_payment_with_general_metadata_and_invalid_from_subaddress(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    invalid_from_subaddress: Optional[bytes],
) -> None:
    """When received a payment with general metadata and invalid from subaddress,
    receiver is not required to take any action on it as long as to subaddress is valid.

    Test Plan:

    1. Generate a valid payment URI from the receiver account.
    2. Create a general metadata with invalid from subaddress and valid to subaddress.
    3. Send payment transaction from sender to receiver on-chain account.
    4. Wait for the transaction executed successfully.
    5. Assert receiver account received funds eventually.

    """

    receiver_uri = receiver_account.generate_payment_uri()
    receiver_account_address: diem_types.AccountAddress = receiver_uri.intent(hrp).account_address

    valid_to_subaddress = receiver_uri.intent(hrp).subaddress
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
    receiver_account.wait_for_balance(currency, amount)


@pytest.mark.parametrize(
    "invalid_from_subaddress", [None, b"", b"bb4a3ba109a3175f", b"subaddress_more_than_8_bytes", b"too_short"]
)
@pytest.mark.parametrize(  # pyre-ignore
    "invalid_to_subaddress", [None, b"", b"bb4a3ba109a3175f", b"subaddress_more_than_8_bytes", b"too_short"]
)
def test_receive_payment_with_general_metadata_and_invalid_subaddresses(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    invalid_to_subaddress: Optional[bytes],
    invalid_from_subaddress: Optional[bytes],
    pending_income_account: AccountResource,
) -> None:
    """When received a payment with general metadata and invalid subaddresses, it is considered
    same with the case received invalid to subaddress, and receiver should refund the payment.

    Test Plan:

    1. Generate a valid payment URI from the receiver account.
    2. Create a general metadata with invalid from subaddress and invalid to subaddress.
    3. Send payment transaction from sender to receiver on-chain account.
    4. Wait for the transaction executed successfully.
    5. Assert sender account received a payment transaction with refund metadata.
    6. Assert receiver account does not receive funds.

    """

    receiver_uri = receiver_account.generate_payment_uri()
    receiver_account_address: diem_types.AccountAddress = receiver_uri.intent(hrp).account_address

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

    pending_income_account.wait_for_event(
        "created_transaction",
        status=Transaction.Status.completed,
        refund_diem_txn_version=original_payment_txn.version,
        refund_reason=RefundReason.invalid_subaddress,
    )
    assert receiver_account.balance(currency) == 0


def test_receive_payment_with_travel_rule_metadata_and_valid_reference_id(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    currency: str,
    hrp: str,
    travel_rule_threshold: int,
) -> None:
    """
    Test Plan:

    1. Generate a valid payment URI from receiver account.
    2. Send a payment meeting travel rule threshold to the payee from the valid payment URI.
    3. Wait for the transaction executed successfully.
    4. Assert receiver account received the fund.

    """

    uri = receiver_account.generate_payment_uri()
    pay = sender_account.send_payment(currency, travel_rule_threshold, payee=uri.intent(hrp).account_id)
    wait_for_payment_transaction_complete(sender_account, pay.id)
    receiver_account.wait_for_balance(currency, travel_rule_threshold)


@pytest.mark.parametrize(  # pyre-ignore
    "invalid_ref_id", [None, "", "ref_id_is_not_uuid", "6cd81d79-f041-4f28-867f-e4d54950833e"]
)
def test_receive_payment_with_travel_rule_metadata_and_invalid_reference_id(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    pending_income_account: AccountResource,
    invalid_ref_id: Optional[str],
) -> None:
    """
    There is no way to create travel rule metadata with invalid reference id when the payment
    amount meets travel rule threshold, because the metadata signature is verified by transaction
    script.
    Also, if metadata signature is provided, transaction script will also verify it regardless
    whether the amount meets travel rule threshold, thus no need to test invalid metadata
    signature case.

    This test bypasses the transaction script validation by sending payment amount under the
    travel rule threshold without metadata signature, and receiver should handle it properly and refund.

    Test Plan:

    1. Generate a valid payment URI from receiver account.
    2. Submit payment under travel rule threshold transaction from sender to receiver on-chain account.
    3. Wait for the transaction executed successfully.
    4. Assert the payment is refund eventually.

    Note: the refund payment will be received by pending income account of the MiniWallet Stub, because
    no account owns the original invalid payment transaction which is sent by test.

    """

    receiver_uri = receiver_account.generate_payment_uri()
    receiver_account_address: diem_types.AccountAddress = receiver_uri.intent(hrp).account_address

    sender_uri = sender_account.generate_payment_uri()
    sender_address = sender_uri.intent(hrp).account_address
    metadata, _ = txnmetadata.travel_rule(invalid_ref_id, sender_address, amount)  # pyre-ignore
    original_payment_txn: jsonrpc.Transaction = stub_config.account.submit_and_wait_for_txn(
        diem_client,
        stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(currency),
            amount=amount,
            payee=receiver_account_address,
            metadata=metadata,
            metadata_signature=b"",
        ),
    )

    pending_income_account.wait_for_event(
        "created_transaction",
        status=Transaction.Status.completed,
        refund_diem_txn_version=original_payment_txn.version,
    )
    assert receiver_account.balance(currency) == 0


@pytest.mark.parametrize("invalid_refund_txn_version", [0, 1, 18446744073709551615])
def test_receive_payment_with_refund_metadata_and_invalid_transaction_version(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: jsonrpc.Client,
    pending_income_account: AccountResource,
    invalid_refund_txn_version: int,
) -> None:
    """
    When received a payment transaction with invalid refund metadata, it's up to wallet
    application to decide how to handle, this test makes sure the wallet application
    should be able to continue to receive following up valid payment transactions.

    Test Plan:

    1. Generate a valid payment URI from receiver account.
    2. Submit payment transaction with refund metadata and invalid txn version.
    3. Wait for the transaction executed successfully.
    4. Send a valid payment to the payment URI.
    5. Assert receiver account received the valid payment.

    """

    receiver_uri = receiver_account.generate_payment_uri()
    receiver_account_address: diem_types.AccountAddress = receiver_uri.intent(hrp).account_address

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

    pay = sender_account.send_payment(currency, amount, payee=receiver_uri.intent(hrp).account_id)
    wait_for_payment_transaction_complete(sender_account, pay.id)
    receiver_account.wait_for_balance(currency, amount)


def wait_for_payment_transaction_complete(account: AccountResource, payment_id: str) -> None:
    # MiniWallet stub generates `updated_transaction` event when transaction is completed on-chain
    # Payment id is same with Transaction id.
    account.wait_for_event("updated_transaction", status=Transaction.Status.completed, id=payment_id)


def test_receive_payment_meets_travel_rule_threshold_both_kyc_data_evaluations_are_accepted(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with minimum valid kyc data with 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "READY"]
    5 . Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="minimum"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_rejected_by_the_receiver(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be rejected by the target wallet application in the stub wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_ABORT"]
    5 . Expect sender and receiver accounts' balances are not changed.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="reject"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_receiver_kyc_data_is_rejected_by_the_sender(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be rejected by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="minimum"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="reject")),
        payment_command_states=["S_INIT", "R_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched by the target wallet application and enough balance in the stub wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "READY"]
    4. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="soft_match"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_receiver_kyc_data_is_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"]
    5. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="minimum"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="soft_match")),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_rejected_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then rejected by the target wallet application in the stub wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="soft_reject"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_receiver_kyc_data_is_soft_match_then_rejected_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched and then rejected by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="minimum"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="soft_reject")),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_receiver_aborts_for_sending_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched by the stub wallet application and 0 balance in the target wallet application.
    3. Setup the stub wallet applicatoin to abort the payment command if receiver requests additional KYC data (soft match).
    4. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    5. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_ABORT"]
    6. Expect sender and receiver accounts' balances are not changed.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="soft_match"),
            reject_additional_kyc_data_request=True,
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_SOFT", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_sender_and_receiver_kyc_data_are_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the target wallet application and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched and then accepted by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"]
    5. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="soft_match"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="soft_match")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_and_accepted_receiver_kyc_data_is_rejected(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the target wallet application and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be rejected by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="soft_match"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="reject")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_and_accepted_receiver_kyc_data_is_soft_match_and_rejected(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the target wallet application and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched and then rejected by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    receive_payment_meets_travel_rule_threshold(
        sender=stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_client.new_kyc_data(sample="soft_match"),
        ),
        receiver=target_client.create_account(kyc_data=stub_client.new_kyc_data(sample="soft_reject")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def receive_payment_meets_travel_rule_threshold(
    sender: AccountResource,
    receiver: AccountResource,
    payment_command_states: List[str],
    currency: str,
    amount: int,
    hrp: str,
    sender_reject_additional_kyc_data_request: bool = False,
) -> None:
    sender_initial = sender.balance(currency)
    receiver_initial = receiver.balance(currency)

    payee = receiver.generate_account_identifier(hrp)
    send_payment = sender.send_payment(currency, amount, payee)
    assert send_payment.currency == currency
    assert send_payment.amount == amount
    assert send_payment.payee == payee

    def match_exchange_states() -> None:
        states = []
        for e in sender.events():
            if e.type in ["created_payment_command", "updated_payment_command"]:
                payment_object = json.loads(e.data)["payment_object"]
                payment = offchain.from_dict(payment_object, offchain.PaymentObject)
                states.append(offchain.payment_state.MACHINE.match_state(payment).id)
        assert states == payment_command_states

    sender.wait_for(match_exchange_states)

    if payment_command_states[-1] == "READY":
        sender.wait_for_balance(currency, sender_initial - amount)
        receiver.wait_for_balance(currency, receiver_initial + amount)
    else:
        sender.wait_for_balance(currency, sender_initial)
        receiver.wait_for_balance(currency, receiver_initial)
