# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


"""This module includes test cases for testing target wallet application sending payment to another wallet.

The onchain accounts of target wallet application should be set up with at least 1_000_000_000_000 coins before running tests.
We can't mint coins for the sending payment onchain account, because depending on implementation details, sending
payment accounts maybe different with the onchain accounts used for receiving payments.
"""


from diem import identifier, offchain
from diem.testing import LocalAccount
from diem.testing.miniwallet import RestClient, AccountResource
from typing import Generator, List
import json, pytest, requests


amount: int = 12345


@pytest.fixture
def sender_account(
    target_client: RestClient, currency: str, travel_rule_threshold: int
) -> Generator[AccountResource, None, None]:
    """sender account for the sending payment test cases

    The account is created on testing target wallet application with initial balance amount equal
    to travel rule threshold number.

    In teardown, `GET /events` API will be called, but failure will be ignored
    as the API is optional for testing target wallet application to implement.
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
    """Generates a new receiver account identifier"""

    return receiver_account.generate_account_identifier(hrp)


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
    receiver_account_identifier = receiver_account.generate_account_identifier(hrp)

    payment = sender_account.send_payment(currency, amount, payee=receiver_account_identifier)
    assert payment.amount == amount
    assert payment.payee == receiver_account_identifier

    sender_account.wait_for_balance(currency, sender_initial_balance - amount)
    receiver_account.wait_for_balance(currency, amount)


def test_send_payment_meets_travel_rule_threshold_both_kyc_data_evaluations_are_accepted(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in target wallet application.
    2. Create receiver account with minimum valid kyc data with 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "READY"]
    5 . Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="minimum")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_rejected_by_the_receiver(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be rejected by the stub wallet application in target wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_ABORT"]
    5 . Expect sender and receiver accounts' balances are not changed.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="reject")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_receiver_kyc_data_is_rejected_by_the_sender(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in target wallet application.
    2. Create receiver account with kyc data that will be rejected by the target wallet application and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="minimum")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="reject")),
        payment_command_states=["S_INIT", "R_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched by the stub wallet application and enough balance in target wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "READY"]
    4. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="soft_match")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_receiver_kyc_data_is_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in target wallet application.
    2. Create receiver account with kyc data that will be soft matched by the target wallet application and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"]
    5. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="minimum")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="soft_match")),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_rejected_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then rejected by the stub wallet application in target wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="soft_reject")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="minimum")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_receiver_kyc_data_is_soft_match_then_rejected_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in target wallet application.
    2. Create receiver account with kyc data that will be soft matched and then rejected by the target wallet application and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="minimum")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="soft_reject")),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_receiver_aborts_for_sending_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in target wallet application.
    2. Create receiver account with kyc data that will be soft matched by the target wallet application and 0 balance in stub wallet application.
    3. Setup the stub wallet applicatoin to abort the payment command if sender requests additional KYC data (soft match).
    4. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    5. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_ABORT"]
    6. Expect sender and receiver accounts' balances are not changed.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="minimum")
        ),
        receiver=stub_client.create_account(
            kyc_data=target_client.new_kyc_data(sample="soft_match"), reject_additional_kyc_data_request=True
        ),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_sender_and_receiver_kyc_data_are_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the stub wallet application and enough balance in target wallet application.
    2. Create receiver account with kyc data that will be soft matched and then accepted by the target wallet application and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"]
    5. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="soft_match")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="soft_match")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_and_accepted_receiver_kyc_data_is_rejected(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the stub wallet application and enough balance in target wallet application.
    2. Create receiver account with kyc data that will be rejected by the target wallet application and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="soft_match")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="reject")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_and_accepted_receiver_kyc_data_is_soft_match_and_rejected(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the stub wallet application and enough balance in target wallet application.
    2. Create receiver account with kyc data that will be soft matched and then rejected by the target wallet application and 0 balance in stub wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    send_payment_meets_travel_rule_threshold(
        sender=target_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.new_kyc_data(sample="soft_match")
        ),
        receiver=stub_client.create_account(kyc_data=target_client.new_kyc_data(sample="soft_reject")),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
        hrp=hrp,
    )


def send_payment_meets_travel_rule_threshold(
    sender: AccountResource,
    receiver: AccountResource,
    payment_command_states: List[str],
    currency: str,
    amount: int,
    hrp: str,
    receiver_reject_additional_kyc_data_request: bool = False,
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
        for e in receiver.events():
            if e.type in ["created_payment_command", "updated_payment_command"]:
                payment_object = json.loads(e.data)["payment_object"]
                payment = offchain.from_dict(payment_object, offchain.PaymentObject)
                states.append(offchain.payment_state.MACHINE.match_state(payment).id)
        assert states == payment_command_states

    receiver.wait_for(match_exchange_states)

    if payment_command_states[-1] == "READY":
        sender.wait_for_balance(currency, sender_initial - amount)
        receiver.wait_for_balance(currency, receiver_initial + amount)
    else:
        sender.wait_for_balance(currency, sender_initial)
        receiver.wait_for_balance(currency, receiver_initial)
