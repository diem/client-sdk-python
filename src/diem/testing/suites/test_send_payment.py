# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


"""This module includes test cases for testing target wallet application sending payment to another wallet.

The onchain accounts of target wallet application should be set up with at least 1_000_000_000_000 coins before running tests.
We can't mint coins for the sending payment onchain account, because depending on implementation details, sending
payment accounts maybe different with the onchain accounts used for receiving payments.
"""


from diem.testing.miniwallet import RestClient, AccountResource
from diem import identifier, LocalAccount
from typing import Generator
import pytest, requests


amount: int = 12345


@pytest.fixture
def sender_account(
    target_client: RestClient, currency: str, travel_rule_threshold: int
) -> Generator[AccountResource, None, None]:
    """sender account for the sending payment test cases

    The account is created on testing target application with initial balance amount equal
    to travel rule threshold number.

    In teardown, `GET /events` API will be called, but failure will be ignored
    as the API is optional for testing target application to implement.
    """

    account = target_client.create_account(balances={currency: travel_rule_threshold * 10})
    yield account
    account.log_events()


@pytest.fixture
def receiver_account(stub_client: RestClient) -> Generator[AccountResource, None, None]:
    """receiver account for the sending payment test cases

    The account is created from stub wallet application.
    In teardown, `GET /events` API will be called, and response result will be printed in log.
    """

    account = stub_client.create_account()
    yield account
    account.log_events()


@pytest.fixture
def receiver_account_identifier(receiver_account: AccountResource, hrp: str) -> str:
    payment_uri = receiver_account.generate_payment_uri()
    return payment_uri.intent(hrp).account_id


@pytest.mark.parametrize("invalid_currency", ["XU", "USD", "xus", "", '"XUS"', "X"])
def test_send_payment_with_invalid_currency(
    sender_account: AccountResource, receiver_account_identifier: str, invalid_currency: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Call send payment `POST /accounts/{account_id}/payments` with invalid currency code.
    3. Expect server response 400 client error, and sender account balance is not changed.
    """

    initial_balances = sender_account.balances()
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        sender_account.send_payment(currency=invalid_currency, amount=amount, payee=receiver_account_identifier)
    assert sender_account.balances() == initial_balances


@pytest.mark.parametrize("invalid_amount", [-1, 0.1])
def test_send_payment_with_invalid_amount(
    sender_account: AccountResource, receiver_account_identifier: str, invalid_amount: float, currency: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Call send payment `POST /accounts/{account_id}/payments` with invalid amount numbers.
    3. Expect server response 400 client error, and sender account balance is not changed.
    """

    initial_balances = sender_account.balances()
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        sender_account.send_payment(
            currency=currency, amount=invalid_amount, payee=receiver_account_identifier  # pyre-ignore
        )
    assert sender_account.balances() == initial_balances


def test_send_payment_with_invalid_account_identifier_as_payee(sender_account: AccountResource, currency: str) -> None:
    """
    Test Plan:

    1. Call send payment `POST /accounts/{account_id}/payments` with `invalid account identifier` as payee.
    2. Expect server response 400 client error, and sender account balance is not changed.
    """

    initial_amount = sender_account.balance(currency)
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        sender_account.send_payment(currency=currency, amount=amount, payee="invalid account identifier")
    assert sender_account.balance(currency) == initial_amount


def test_send_payment_with_invalid_account_identifier_checksum_as_payee(
    sender_account: AccountResource, receiver_account_identifier: str, currency: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Manuplate valid account identifier's checksum chars.
    3. Call send payment `POST /accounts/{account_id}/payments` with invalid account identifier.
    4. Expect server response 400 client error, and sender account balance is not changed.
    """

    initial_amount = sender_account.balance(currency)
    invalid_account_identifier = receiver_account_identifier[:-6] + "000000"
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        sender_account.send_payment(currency=currency, amount=amount, payee=invalid_account_identifier)
    assert sender_account.balance(currency) == initial_amount


def test_send_payment_with_invalid_account_identifier_hrp_as_payee(
    sender_account: AccountResource, receiver_account_identifier: str, currency: str, hrp: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Extract account onchain address and subaddress from receiving payment account identifier.
    3. Use a different hrp and extracted account address and subaddress to create a new account identifier.
    4. Call send payment `POST /accounts/{account_id}/payments` with created account identifier.
    5. Expect server response 400 client error, and sender account balance is not changed.
    """

    initial_amount = sender_account.balance(currency)
    account_address, subaddress = identifier.decode_account(receiver_account_identifier, hrp)
    new_hrp = identifier.TDM if hrp != identifier.TDM else identifier.PDM
    new_account_identifier = identifier.encode_account(account_address, subaddress, new_hrp)
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        sender_account.send_payment(currency=currency, amount=amount, payee=new_account_identifier)
    assert sender_account.balance(currency) == initial_amount


def test_send_payment_with_invalid_account_identifier_onchain_account_address_as_payee(
    sender_account: AccountResource, receiver_account_identifier: str, currency: str, hrp: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Extract account onchain address and subaddress from receiving payment account identifier.
    3. Use an invalid onchain account address and extracted subaddress to create a new account identifier.
    4. Call send payment `POST /accounts/{account_id}/payments` with created account identifier.
    5. Expect server response 400 client error, and sender account balance is not changed.
    """

    initial_amount = sender_account.balance(currency)
    _, subaddress = identifier.decode_account(receiver_account_identifier, hrp)
    invalid_account_address = LocalAccount().account_address
    invalid_account_identifier = identifier.encode_account(invalid_account_address, subaddress, hrp)
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        sender_account.send_payment(currency=currency, amount=amount, payee=invalid_account_identifier)
    assert sender_account.balance(currency) == initial_amount


def test_send_payment_with_an_amount_exceeding_account_balance(
    sender_account: AccountResource, receiver_account_identifier: str, currency: str, hrp: str
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Get sender account balance.
    3. Call send payment `POST /accounts/{account_id}/payments` with amount = sender account balance + 1.
    4. Expect server response 400 client error, and sender account balance is not changed.
    """

    initial_amount = sender_account.balance(currency)
    amount = initial_amount + 1
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        sender_account.send_payment(currency=currency, amount=amount, payee=receiver_account_identifier)
    assert sender_account.balance(currency) == initial_amount


@pytest.mark.parametrize("amount", [1, 123456, 125555])
def test_send_payment_with_valid_inputs_under_the_travel_rule_threshold(
    sender_account: AccountResource,
    receiver_account: AccountResource,
    receiver_account_identifier: str,
    amount: int,
    currency: str,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Generate valid receive payment account identifier.
    2. Call send payment `POST /accounts/{account_id}/payments` with the account identifier.
    3. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    initial_amount = sender_account.balance(currency)
    assert receiver_account.balance(currency) == 0

    sender_account.send_payment(currency=currency, amount=amount, payee=receiver_account_identifier)

    receiver_account.wait_for_balance(currency, amount)
    sender_account.wait_for_balance(currency, initial_amount - amount)


@pytest.mark.parametrize(
    "amount",
    [
        1,
        999_999_999,
        1_000_000_000,
        2_000_000_000,
    ],
)
def test_send_payment_to_the_other_account_in_the_same_wallet(
    sender_account: AccountResource, target_client: RestClient, currency: str, amount: int, hrp: str
) -> None:
    """
    Test Plan:

    1. Create 2 accounts in target wallet application, one for sender, one for receiver.
    2. Generate valid receive payment account identifier from the receiver account.
    3. Send payment from sender account to receiver account.
    4. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    sender_initial_balance = sender_account.balance(currency)
    receiver_account = target_client.create_account()
    receiver_account_identifier = receiver_account.generate_payment_uri().intent(hrp).account_id

    payment = sender_account.send_payment(currency, amount, payee=receiver_account_identifier)
    assert payment.amount == amount
    assert payment.payee == receiver_account_identifier

    sender_account.wait_for_balance(currency, sender_initial_balance - amount)
    receiver_account.wait_for_balance(currency, amount)
