# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import Account, Transaction, RestClient
from typing import Optional, Dict, Any, Union
from .envs import should_test_debug_api, is_self_check
from .clients import Clients
import pytest, requests, time, json


def test_create_account_resource_without_balance(target_client: RestClient) -> None:
    account = target_client.create_account()
    assert account.balances() == {}


def test_create_account_with_kyc_data_and_balances(target_client: RestClient, currency: str) -> None:
    kyc_data = target_client.new_kyc_data()
    account = target_client.create_account(kyc_data=kyc_data, balances={currency: 100})
    assert account.id
    assert account.kyc_data == kyc_data
    assert account.balances() == {currency: 100}
    assert account.balance(currency) == 100


@pytest.mark.parametrize(  # pyre-ignore
    "err_msg, kyc_data",
    [
        ("'kyc_data' must be JSON-encoded KycDataObject", "invalid json"),
        ("'kyc_data' must be JSON-encoded KycDataObject", "{}"),
        ("'kyc_data' type must be 'str'", {}),
    ],
)
def test_create_account_with_invalid_kyc_data(
    target_client: RestClient, currency: str, err_msg: str, kyc_data: Union[str, Dict[str, Any]]
) -> None:
    with pytest.raises(requests.exceptions.HTTPError, match="400 Client Error") as einfo:
        target_client.create("/accounts", kyc_data=kyc_data)
    if is_self_check():
        assert err_msg in einfo.value.response.text


@pytest.mark.parametrize(
    "err_msg, balances",
    [
        ("'currency' is invalid", {"invalid": 11}),
        ("'currency' is invalid", {22: 11}),
        ("'amount' value must be greater than or equal to zero", {"XUS": -11}),
        ("'amount' type must be 'int'", {"XUS": "11"}),
    ],
)
def test_create_account_with_invalid_balances(
    target_client: RestClient, currency: str, err_msg: str, balances: Optional[Dict[str, int]]
) -> None:
    kyc_data = target_client.new_kyc_data()

    with pytest.raises(requests.exceptions.HTTPError, match="400 Client Error") as einfo:
        target_client.create("/accounts", kyc_data=kyc_data, balances=balances)
    if is_self_check():
        assert err_msg in einfo.value.response.text


def test_create_account_payment_uri(target_client: RestClient, hrp: str) -> None:
    account = target_client.create_account()
    ret = account.create_payment_uri()
    assert ret.account_id == account.id
    intent = ret.intent(hrp)
    assert intent.account_address
    assert intent.subaddress


def test_send_payment_and_events(clients: Clients, hrp: str, currency: str) -> None:
    receiver = clients.target.create_account()
    payment_uri = receiver.create_payment_uri()

    amount = 1234
    sender = clients.stub.create_account(balances={currency: amount})
    assert sender.balance(currency) == amount

    index = len(sender.events())
    payment = sender.send_payment(currency, amount, payment_uri.intent(hrp).account_id)
    assert payment.account_id == sender.id
    assert payment.currency == currency
    assert payment.amount == amount
    assert payment.payee == payment_uri.intent(hrp).account_id

    sender.wait_for_balance(currency, 0)
    sender.wait_for_event("updated_transaction", status=Transaction.Status.completed, start_index=index)

    receiver.wait_for_balance(currency, amount)

    new_events = [e for e in sender.events(index) if e.type != "info"]
    assert len(new_events) == 4, new_events
    assert new_events[0].type == "created_transaction"
    assert new_events[1].type == "updated_transaction"
    assert sorted(list(json.loads(new_events[1].data).keys())) == ["id", "subaddress_hex"]
    assert new_events[2].type == "updated_transaction"
    assert sorted(list(json.loads(new_events[2].data).keys())) == ["id", "signed_transaction"]
    assert new_events[3].type == "updated_transaction"
    assert sorted(list(json.loads(new_events[3].data).keys())) == ["diem_transaction_version", "id", "status"]


def test_receive_payment_and_events(clients: Clients, currency: str, hrp: str) -> None:
    receiver = clients.stub.create_account()
    payment_uri = receiver.create_payment_uri()

    index = len(receiver.events())
    amount = 1234
    sender = clients.target.create_account({currency: amount})
    payment = sender.send_payment(currency, amount, payment_uri.intent(hrp).account_id)

    receiver.wait_for_balance(currency, amount)
    sender.wait_for_balance(currency, 0)

    new_events = [e for e in receiver.events(index) if e.type != "info"]
    assert len(new_events) == 1
    assert new_events[0].type == "created_transaction"
    txn = Transaction(**json.loads(new_events[0].data))
    assert txn.id
    assert txn.currency == payment.currency
    assert txn.amount == payment.amount
    assert txn.diem_transaction_version


def test_receive_multiple_payments(clients: Clients, hrp: str, currency: str) -> None:
    receiver = clients.stub.create_account()
    payment_uri = receiver.create_payment_uri()

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


@pytest.mark.parametrize(
    "invalid_payee",
    [
        "invalid id",
        "dm1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqqd8p9cq",
        "tdm1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqqv88j4x",
    ],
)
def test_send_payment_payee_is_invalid(clients: Clients, currency: str, invalid_payee: str, hrp: str) -> None:
    sender = clients.stub.create_account({currency: 100})

    index = len(sender.events())
    with pytest.raises(requests.exceptions.HTTPError, match="400 Client Error") as einfo:
        sender.send_payment(currency, 1, invalid_payee)

    if is_self_check():
        assert "'payee' is invalid account identifier" in einfo.value.response.text

    assert sender.balance(currency) == 100
    assert sender.events(index) == []


def test_return_client_error_if_send_payment_more_than_account_balance(
    clients: Clients, currency: str, hrp: str
) -> None:
    receiver = clients.target.create_account()
    payment_uri = receiver.create_payment_uri()
    sender = clients.stub.create_account({currency: 100})

    index = len(sender.events())
    with pytest.raises(requests.exceptions.HTTPError, match="400 Client Error") as einfo:
        sender.send_payment(currency, 101, payment_uri.intent(hrp).account_id)
    if is_self_check():
        assert "account balance not enough" in einfo.value.response.text
    assert sender.balance(currency) == 100
    assert sender.events(index) == []


def test_send_payment_meets_travel_rule_limit(
    clients: Clients, currency: str, travel_rule_threshold: int, hrp: str
) -> None:
    amount = travel_rule_threshold
    receiver = clients.target.create_account()
    payment_uri = receiver.create_payment_uri()
    sender = clients.stub.create_account({currency: amount}, kyc_data=clients.stub.new_kyc_data())
    payment = sender.send_payment(currency, amount, payee=payment_uri.intent(hrp).account_id)

    sender.wait_for_event("updated_transaction", id=payment.id, status=Transaction.Status.completed)
    sender.wait_for_balance(currency, 0)
    receiver.wait_for_balance(currency, travel_rule_threshold)


def test_account_balance_validation_should_exclude_canceled_transactions(
    clients: Clients, currency: str, travel_rule_threshold: int, hrp: str
) -> None:
    amount = travel_rule_threshold
    receiver = clients.target.create_account()
    payment_uri = receiver.create_payment_uri()
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
    payment_uri = receiver.create_payment_uri()
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
    ret = account.create_payment_uri()
    assert ret
    assert len(account.events(index)) == 1
    assert account.events(index)[0].type == "created_payment_uri"


@pytest.mark.skipif(bool(not is_self_check()), reason="self check is not enabled")
def test_openapi_spec(target_client: RestClient) -> None:
    resp = target_client.send("GET", "/openapi.yaml")
    assert resp.text
