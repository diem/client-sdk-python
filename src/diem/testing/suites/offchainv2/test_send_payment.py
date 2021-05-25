# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


"""This module includes test cases for testing target wallet application sending payment to another wallet.

The onchain accounts of target wallet application should be set up with at least 1_000_000_000_000 coins before running tests.
We can't mint coins for the sending payment onchain account, because depending on implementation details, sending
payment accounts maybe different with the onchain accounts used for receiving payments.
"""


from diem import offchain
from diem.testing.miniwallet import RestClient, AccountResource
from typing import List
from ..conftest import wait_for, wait_for_balance
import json


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

    wait_for(match_exchange_states)

    if payment_command_states[-1] == "READY":
        wait_for_balance(sender, currency, sender_initial - amount)
        wait_for_balance(receiver, currency, receiver_initial + amount)
    else:
        wait_for_balance(sender, currency, sender_initial)
        wait_for_balance(receiver, currency, receiver_initial)
