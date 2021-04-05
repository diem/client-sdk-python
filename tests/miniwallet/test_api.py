# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import RestClient, Account
import pytest, requests, json, time


def test_create_account_with_balances_and_kyc_data(target_client: RestClient, currency: str) -> None:
    kyc_data = target_client.new_kyc_data(sample="minimum")
    balances = {currency: 123}
    account = target_client.create_account(balances, kyc_data=kyc_data)
    assert account.kyc_data == kyc_data
    assert account.balances() == balances


@pytest.mark.parametrize(
    "kyc_data",
    [
        "invalid json",
        '{"type": "individual"}',
        '{"type": "entity"}',
        '{"payload_version": 1}',
        '{"type": "individual", "payload_version": "1"}',
    ],
)
def test_create_an_account_with_invalid_kyc_data(target_client: RestClient, kyc_data: str) -> None:
    with pytest.raises(requests.exceptions.HTTPError, match="400 Client Error") as einfo:
        target_client.create("/accounts", kyc_data=kyc_data)

    assert "'kyc_data' must be JSON-encoded KycDataObject" in einfo.value.response.text


@pytest.mark.parametrize(
    "balances, err_msg",
    [
        ('{"XUS": -1}', "'amount' value must be greater than or equal to zero"),
        ('{"DDD": 100}', "'currency' is invalid"),
        ('{"XUS": 100, "DDD": 100}', "'currency' is invalid"),
        ('{"XUS": 100, "DDD": -1}', "'currency' is invalid"),
        ('{"XUS": "100"}', "'amount' type must be 'int'"),
        ('{"currency": "XUS", "amount": 123}', "'currency' is invalid"),
        ('{"XUS": 23423423423432423434234234324233423}', "'amount' value is too big"),
    ],
)
def test_create_an_account_with_invalid_initial_deposit_balance_currency(
    target_client: RestClient, balances: str, err_msg
) -> None:
    with pytest.raises(requests.exceptions.HTTPError, match="400 Client Error") as einfo:
        target_client.create("/accounts", balances=json.loads(balances))

    assert err_msg in einfo.value.response.text


def test_receive_multiple_payments(target_client: RestClient, stub_client: RestClient, hrp: str, currency: str) -> None:
    receiver = stub_client.create_account()
    payment_uri = receiver.generate_payment_uri()

    index = len(receiver.events())
    amount = 1234
    sender1 = target_client.create_account({currency: amount})
    sender1.send_payment(currency, amount, payment_uri.intent(hrp).account_id)

    sender2 = target_client.create_account({currency: amount})
    sender2.send_payment(currency, amount, payment_uri.intent(hrp).account_id)

    sender1.wait_for_balance(currency, 0)
    sender2.wait_for_balance(currency, 0)
    receiver.wait_for_balance(currency, amount * 2)

    new_events = [e for e in receiver.events(index) if e.type != "info"]
    assert len(new_events) == 2
    assert new_events[0].type == "created_transaction"
    assert new_events[1].type == "created_transaction"


def test_account_balance_validation_should_exclude_canceled_transactions(
    target_client: RestClient, stub_client: RestClient, currency: str, travel_rule_threshold: int, hrp: str
) -> None:
    amount = travel_rule_threshold
    receiver = target_client.create_account()
    payment_uri = receiver.generate_payment_uri()
    sender = stub_client.create_account({currency: amount}, kyc_data=target_client.new_reject_kyc_data())
    # payment should be rejected during offchain kyc data exchange
    payment = sender.send_payment(currency, amount, payee=payment_uri.intent(hrp).account_id)

    sender.wait_for_event("updated_transaction", id=payment.id, status="canceled")

    sender.send_payment(currency, travel_rule_threshold - 1, payment_uri.intent(hrp).account_id)

    receiver.wait_for_balance(currency, travel_rule_threshold - 1)
    sender.wait_for_balance(currency, 1)


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


def test_create_account_payment_uri_events(target_client: RestClient, hrp: str) -> None:
    account = target_client.create_account()
    index = len(account.events())
    ret = account.generate_payment_uri()
    assert ret
    assert len(account.events(index)) == 1
    assert account.events(index)[0].type == "created_subaddress"


def test_openapi_spec(target_client: RestClient) -> None:
    resp = target_client.send("GET", "/openapi.yaml")
    assert resp.text
