# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem.testing.miniwallet import Event, AccountResource
from diem import offchain
from typing import List
from .clients import Clients
import pytest, json


@pytest.mark.parametrize("amount", [1, 999_999])
@pytest.mark.parametrize("actor", ["sender", "receiver"])
def test_payment_under_threshold_succeed(
    actor: str,
    amount: int,
    currency: str,
    clients: Clients,
    hrp: str,
) -> None:
    sender_client = clients.target if actor == "sender" else clients.stub
    receiver_client = clients.stub if actor == "sender" else clients.target

    sender = sender_client.create_account({currency: amount})
    receiver = receiver_client.create_account()
    sender_initial = sender.balance(currency)
    receiver_initial = receiver.balance(currency)

    payment_uri = receiver.create_payment_uri()
    send_payment = sender.send_payment(currency, amount, payment_uri.intent(hrp).account_id)
    assert send_payment.currency == currency
    assert send_payment.amount == amount
    assert send_payment.payee == payment_uri.intent(hrp).account_id

    sender.wait_for_balance(currency, sender_initial - amount)
    receiver.wait_for_balance(currency, receiver_initial + amount)


@pytest.mark.parametrize(
    "sender_kyc, receiver_kyc, exchange_states, payment_result",
    [
        ("valid_kyc_data", "valid_kyc_data", ["S_INIT", "R_SEND", "READY"], "completed"),
        (
            "valid_kyc_data",
            "soft_match_kyc_data",
            ["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
            "completed",
        ),
        ("valid_kyc_data", "reject_kyc_data", ["S_INIT", "R_SEND", "S_ABORT"], "failed"),
        (
            "valid_kyc_data",
            "soft_reject_kyc_data",
            ["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
            "failed",
        ),
        (
            "soft_match_kyc_data",
            "valid_kyc_data",
            ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "READY"],
            "completed",
        ),
        (
            "soft_match_kyc_data",
            "soft_match_kyc_data",
            ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
            "completed",
        ),
        (
            "soft_match_kyc_data",
            "reject_kyc_data",
            ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_ABORT"],
            "failed",
        ),
        (
            "soft_match_kyc_data",
            "soft_reject_kyc_data",
            ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
            "failed",
        ),
        ("reject_kyc_data", "valid_kyc_data", ["S_INIT", "R_ABORT"], "failed"),
        ("reject_kyc_data", "soft_match_kyc_data", ["S_INIT", "R_ABORT"], "failed"),
        ("reject_kyc_data", "reject_kyc_data", ["S_INIT", "R_ABORT"], "failed"),
        ("reject_kyc_data", "soft_reject_kyc_data", ["S_INIT", "R_ABORT"], "failed"),
        (
            "soft_reject_kyc_data",
            "valid_kyc_data",
            ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"],
            "failed",
        ),
        (
            "soft_reject_kyc_data",
            "soft_match_kyc_data",
            ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"],
            "failed",
        ),
        (
            "soft_reject_kyc_data",
            "reject_kyc_data",
            ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"],
            "failed",
        ),
        (
            "soft_reject_kyc_data",
            "soft_reject_kyc_data",
            ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"],
            "failed",
        ),
    ],
)
@pytest.mark.parametrize("actor", ["sender", "receiver"])
def test_payment_meets_travel_rule_threshold(
    actor: str,
    sender_kyc: str,
    receiver_kyc: str,
    exchange_states: List[str],
    payment_result: str,
    currency: str,
    travel_rule_threshold: int,
    clients: Clients,
    hrp: str,
) -> None:
    amount = travel_rule_threshold
    sender_client = clients.target if actor == "sender" else clients.stub
    receiver_client = clients.stub if actor == "sender" else clients.target

    sender = sender_client.create_account(
        {currency: amount}, kyc_data=getattr(receiver_client, "new_%s" % sender_kyc)()
    )
    receiver = receiver_client.create_account(kyc_data=getattr(sender_client, "new_%s" % receiver_kyc)())
    sender_initial = sender.balance(currency)
    receiver_initial = receiver.balance(currency)

    payment_uri = receiver.create_payment_uri()
    send_payment = sender.send_payment(currency, amount, payment_uri.intent(hrp).account_id)
    assert send_payment.currency == currency
    assert send_payment.amount == amount
    assert send_payment.payee == payment_uri.intent(hrp).account_id

    stub_account: AccountResource = sender if clients.stub == sender.client else receiver

    def match_exchange_states() -> None:
        assert payment_command_event_states(stub_account) == exchange_states

    stub_account.wait_for(match_exchange_states)

    if payment_result == "completed":
        sender.wait_for_balance(currency, sender_initial - amount)
        receiver.wait_for_balance(currency, receiver_initial + amount)
    else:
        sender.wait_for_balance(currency, sender_initial)
        receiver.wait_for_balance(currency, receiver_initial)


def payment_state_id(event: Event) -> str:
    payment = offchain.from_dict(json.loads(event.data)["payment_object"], offchain.PaymentObject)
    return offchain.payment_state.MACHINE.match_state(payment).id


def payment_command_event_states(account: AccountResource) -> List[str]:
    return [payment_state_id(event) for event in account.events() if is_payment_command_event(event)]


def is_payment_command_event(e: Event) -> bool:
    return e.type in ["created_payment_command", "updated_payment_command"]
