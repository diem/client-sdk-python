# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import Account, Transaction, RestClient
from .envs import should_test_debug_api, is_self_check
from .clients import Clients
import pytest, time, json


def test_receive_multiple_payments(clients: Clients, hrp: str, currency: str) -> None:
    receiver = clients.stub.create_account()
    payment_uri = receiver.generate_payment_uri()

    index = len(receiver.events())
    amount = 1234
    sender1 = clients.target.create_account({currency: amount})
    sender1.send_payment(currency, amount, payment_uri.intent(hrp).account_id)

    sender2 = clients.target.create_account({currency: amount})
    sender2.send_payment(currency, amount, payment_uri.intent(hrp).account_id)

    sender1.wait_for_balance(currency, 0)
    sender2.wait_for_balance(currency, 0)
    receiver.wait_for_balance(currency, amount * 2)

    new_events = [e for e in receiver.events(index) if e.type != "info"]
    assert len(new_events) == 2
    assert new_events[0].type == "created_transaction"
    assert new_events[1].type == "created_transaction"


def test_account_balance_validation_should_exclude_canceled_transactions(
    clients: Clients, currency: str, travel_rule_threshold: int, hrp: str
) -> None:
    amount = travel_rule_threshold
    receiver = clients.target.create_account()
    payment_uri = receiver.generate_payment_uri()
    sender = clients.stub.create_account({currency: amount}, kyc_data=clients.target.new_reject_kyc_data())
    # payment should be rejected during offchain kyc data exchange
    payment = sender.send_payment(currency, amount, payee=payment_uri.intent(hrp).account_id)

    sender.wait_for_event("updated_transaction", id=payment.id, status=Transaction.Status.canceled)

    sender.send_payment(currency, travel_rule_threshold - 1, payment_uri.intent(hrp).account_id)

    receiver.wait_for_balance(currency, travel_rule_threshold - 1)
    sender.wait_for_balance(currency, 1)


@pytest.mark.parametrize(
    "amount",
    [
        0,
        1,
        1_000_000_000,
        1_000_000_000_000,
    ],
)
def test_internal_transfer(clients: Clients, currency: str, amount: int, hrp: str) -> None:
    receiver = clients.stub.create_account()
    payment_uri = receiver.generate_payment_uri()
    sender = clients.stub.create_account({currency: amount})

    index = len(sender.events())

    payment = sender.send_payment(currency, amount, payee=payment_uri.intent(hrp).account_id)
    assert payment.amount == amount
    assert payment.payee == payment_uri.intent(hrp).account_id

    sender.wait_for_event("updated_transaction", start_index=index, id=payment.id, status=Transaction.Status.completed)

    sender.wait_for_balance(currency, 0)
    receiver.wait_for_balance(currency, amount)


@pytest.mark.skipif(bool(not should_test_debug_api()), reason="test debug api is not enabled")
def test_create_account_event(target_client: RestClient, currency: str) -> None:
    before_timestamp = int(time.time() * 1000)
    account = target_client.create_account()
    after_timestamp = int(time.time() * 1000)

    events = account.events()
    assert len(events) == 1
    event = events[0]
    assert event.id
    assert event.timestamp >= before_timestamp
    assert event.timestamp <= after_timestamp
    assert event.type == "created_account"
    event_data = Account(**json.loads(event.data))
    assert event_data.kyc_data == account.kyc_data
    assert event_data.id == account.id


@pytest.mark.skipif(bool(not should_test_debug_api()), reason="test debug api is not enabled")
def test_create_account_payment_uri_events(target_client: RestClient, hrp: str) -> None:
    account = target_client.create_account()
    index = len(account.events())
    ret = account.generate_payment_uri()
    assert ret
    assert len(account.events(index)) == 1
    assert account.events(index)[0].type == "created_payment_uri"


@pytest.mark.skipif(bool(not is_self_check()), reason="self check is not enabled")
def test_openapi_spec(target_client: RestClient) -> None:
    resp = target_client.send("GET", "/openapi.yaml")
    assert resp.text
