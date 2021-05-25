# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


"""This module includes test cases for testing target wallet application sending payment to another wallet.

The onchain accounts of target wallet application should be set up with at least 1_000_000_000_000 coins before running tests.
We can't mint coins for the sending payment onchain account, because depending on implementation details, sending
payment accounts maybe different with the onchain accounts used for receiving payments.
"""


from diem import identifier
from diem.testing import LocalAccount
from diem.testing.miniwallet import RestClient
from ..conftest import wait_for_balance
import pytest, requests


@pytest.mark.parametrize("invalid_currency", ["XU", "USD", "xus", "", '"XUS"', "X"])
def test_send_payment_with_invalid_currency(
    stub_client: RestClient, target_client: RestClient, invalid_currency: str, currency: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Call send payment `POST /accounts/{account_id}/payments` with invalid currency code.
    3. Expect server response 400 client error, and sender account balance is not changed.
    """

    amount = 1_000_000
    sender_account = target_client.create_account(balances={currency: amount})
    receiver_account = stub_client.create_account()
    try:
        initial_balances = sender_account.balances()
        receiver_account_identifier = receiver_account.generate_account_identifier()
        with pytest.raises(requests.HTTPError, match="400 Client Error"):
            sender_account.send_payment(currency=invalid_currency, amount=amount, payee=receiver_account_identifier)
        assert sender_account.balances() == initial_balances
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize("invalid_amount", [-1, 0.1])
def test_send_payment_with_invalid_amount(
    stub_client: RestClient, target_client: RestClient, invalid_amount: float, currency: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Call send payment `POST /accounts/{account_id}/payments` with invalid amount numbers.
    3. Expect server response 400 client error, and sender account balance is not changed.
    """

    amount = 1_000_000
    sender_account = target_client.create_account(balances={currency: amount})
    receiver_account = stub_client.create_account()
    try:
        initial_balances = sender_account.balances()
        receiver_account_identifier = receiver_account.generate_account_identifier()
        with pytest.raises(requests.HTTPError, match="400 Client Error"):
            sender_account.send_payment(
                currency=currency, amount=invalid_amount, payee=receiver_account_identifier  # pyre-ignore
            )
        assert sender_account.balances() == initial_balances
    finally:
        receiver_account.log_events()
        sender_account.log_events()


def test_send_payment_with_invalid_account_identifier_as_payee(target_client: RestClient, currency: str) -> None:
    """
    Test Plan:

    1. Call send payment `POST /accounts/{account_id}/payments` with `invalid account identifier` as payee.
    2. Expect server response 400 client error, and sender account balance is not changed.
    """

    amount = 1_000_000
    sender_account = target_client.create_account(balances={currency: amount})
    try:
        with pytest.raises(requests.HTTPError, match="400 Client Error"):
            sender_account.send_payment(currency=currency, amount=amount, payee="invalid account identifier")
        assert sender_account.balance(currency) == amount
    finally:
        sender_account.log_events()


def test_send_payment_with_invalid_account_identifier_checksum_as_payee(
    stub_client: RestClient, target_client: RestClient, currency: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Manuplate valid account identifier's checksum chars.
    3. Call send payment `POST /accounts/{account_id}/payments` with invalid account identifier.
    4. Expect server response 400 client error, and sender account balance is not changed.
    """

    amount = 1_000_000
    sender_account = target_client.create_account(balances={currency: amount})
    receiver_account = stub_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        invalid_account_identifier = receiver_account_identifier[:-6] + "000000"
        with pytest.raises(requests.HTTPError, match="400 Client Error"):
            sender_account.send_payment(currency=currency, amount=amount, payee=invalid_account_identifier)
        assert sender_account.balance(currency) == amount
    finally:
        receiver_account.log_events()
        sender_account.log_events()


def test_send_payment_with_invalid_account_identifier_hrp_as_payee(
    stub_client: RestClient, target_client: RestClient, currency: str, hrp: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Extract account onchain address and subaddress from receiving payment account identifier.
    3. Use a different hrp and extracted account address and subaddress to create a new account identifier.
    4. Call send payment `POST /accounts/{account_id}/payments` with created account identifier.
    5. Expect server response 400 client error, and sender account balance is not changed.
    """

    amount = 1_000_000
    sender_account = target_client.create_account(balances={currency: amount})
    receiver_account = stub_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        account_address, subaddress = identifier.decode_account(receiver_account_identifier, hrp)
        new_hrp = identifier.TDM if hrp != identifier.TDM else identifier.PDM
        new_account_identifier = identifier.encode_account(account_address, subaddress, new_hrp)
        with pytest.raises(requests.HTTPError, match="400 Client Error"):
            sender_account.send_payment(currency=currency, amount=amount, payee=new_account_identifier)
        assert sender_account.balance(currency) == amount
    finally:
        receiver_account.log_events()
        sender_account.log_events()


def test_send_payment_with_invalid_account_identifier_onchain_account_address_as_payee(
    stub_client: RestClient, target_client: RestClient, currency: str, hrp: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Extract account onchain address and subaddress from receiving payment account identifier.
    3. Use an invalid onchain account address and extracted subaddress to create a new account identifier.
    4. Call send payment `POST /accounts/{account_id}/payments` with created account identifier.
    5. Expect server response 400 client error, and sender account balance is not changed.
    """

    amount = 1_000_000
    sender_account = target_client.create_account(balances={currency: amount})
    receiver_account = stub_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        _, subaddress = identifier.decode_account(receiver_account_identifier, hrp)
        invalid_account_address = LocalAccount().account_address
        invalid_account_identifier = identifier.encode_account(invalid_account_address, subaddress, hrp)
        with pytest.raises(requests.HTTPError, match="400 Client Error"):
            sender_account.send_payment(currency=currency, amount=amount, payee=invalid_account_identifier)
        assert sender_account.balance(currency) == amount
    finally:
        receiver_account.log_events()
        sender_account.log_events()


def test_send_payment_with_an_amount_exceeding_account_balance(
    stub_client: RestClient, target_client: RestClient, currency: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Get sender account balance.
    3. Call send payment `POST /accounts/{account_id}/payments` with amount = sender account balance + 1.
    4. Expect server response 400 client error, and sender account balance is not changed.
    """

    amount = 1_000_000
    sender_account = target_client.create_account(balances={currency: amount})
    receiver_account = stub_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        with pytest.raises(requests.HTTPError, match="400 Client Error"):
            sender_account.send_payment(currency=currency, amount=amount + 1, payee=receiver_account_identifier)
        assert sender_account.balance(currency) == amount
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize("amount", [10_000, 56_780_000, 120_000])
def test_send_payment_with_valid_inputs_under_the_travel_rule_threshold(
    stub_client: RestClient,
    target_client: RestClient,
    amount: int,
    currency: str,
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Call send payment `POST /accounts/{account_id}/payments` with the account identifier.
    3. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    sender_account = target_client.create_account(balances={currency: amount})
    receiver_account = stub_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        sender_account.send_payment(currency=currency, amount=amount, payee=receiver_account_identifier)

        wait_for_balance(receiver_account, currency, amount)
        wait_for_balance(sender_account, currency, 0)
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize(
    "amount",
    [
        10_000,
        999_990_000,
        1_000_000_000,
        2_000_000_000,
    ],
)
def test_send_payment_to_the_other_account_in_the_same_wallet(
    target_client: RestClient,
    currency: str,
    amount: int,
) -> None:
    """
    Test Plan:

    1. Create 2 accounts in target wallet application, one for sender, one for receiver.
    2. Generate valid receive payment account identifier from the receiver account.
    3. Send payment from sender account to receiver account.
    4. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    sender_account = target_client.create_account(balances={currency: amount})
    receiver_account = target_client.create_account()
    try:
        receiver_account_identifier = receiver_account.generate_account_identifier()
        sender_account.send_payment(currency, amount, payee=receiver_account_identifier)
        wait_for_balance(sender_account, currency, 0)
        wait_for_balance(receiver_account, currency, amount)
    finally:
        receiver_account.log_events()
        sender_account.log_events()
