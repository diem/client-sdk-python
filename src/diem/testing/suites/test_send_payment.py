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
from typing import List
import json, pytest, requests


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

        receiver_account.wait_for_balance(currency, amount)
        sender_account.wait_for_balance(currency, 0)
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
        sender_account.wait_for_balance(currency, 0)
        receiver_account.wait_for_balance(currency, amount)
    finally:
        receiver_account.log_events()
        sender_account.log_events()


def test_send_payment_meets_travel_rule_threshold_both_kyc_data_evaluations_are_accepted(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().minimum
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().minimum),
        payment_command_states=["S_INIT", "R_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_rejected_by_the_receiver(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().reject
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().minimum),
        payment_command_states=["S_INIT", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_receiver_kyc_data_is_rejected_by_the_sender(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().minimum
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().reject),
        payment_command_states=["S_INIT", "R_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().soft_match
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().minimum),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_receiver_kyc_data_is_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().minimum
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().soft_match),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_rejected_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().soft_reject
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().minimum),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_receiver_kyc_data_is_soft_match_then_rejected_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().minimum
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().soft_reject),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_receiver_aborts_for_sending_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().minimum
        ),
        receiver=stub_client.create_account(
            kyc_data=target_client.get_kyc_sample().soft_match, reject_additional_kyc_data_request=True
        ),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_sender_and_receiver_kyc_data_are_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().soft_match
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().soft_match),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_and_accepted_receiver_kyc_data_is_rejected(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().soft_match
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().reject),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def test_send_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_and_accepted_receiver_kyc_data_is_soft_match_and_rejected(
    currency: str,
    travel_rule_threshold: int,
    target_client: RestClient,
    stub_client: RestClient,
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
            balances={currency: travel_rule_threshold}, kyc_data=stub_client.get_kyc_sample().soft_match
        ),
        receiver=stub_client.create_account(kyc_data=target_client.get_kyc_sample().soft_reject),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


def send_payment_meets_travel_rule_threshold(
    sender: AccountResource,
    receiver: AccountResource,
    payment_command_states: List[str],
    currency: str,
    amount: int,
    receiver_reject_additional_kyc_data_request: bool = False,
) -> None:
    sender_initial = sender.balance(currency)
    receiver_initial = receiver.balance(currency)

    payee = receiver.generate_account_identifier()
    sender.send_payment(currency, amount, payee)

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
