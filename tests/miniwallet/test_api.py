# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import RestClient, Account
from diem import utils, identifier
from typing import Dict, Any
from diem.testing.suites.conftest import wait_for_balance, wait_for_event
import pytest, json, time, aiohttp


pytestmark = pytest.mark.asyncio  # pyre-ignore


async def test_create_account_with_balances_and_kyc_data(target_client: RestClient, currency: str) -> None:
    kyc = await target_client.get_kyc_sample()
    balances = {currency: 123}
    account = await target_client.create_account(balances, kyc_data=kyc.minimum)
    assert account.kyc_data == kyc.minimum
    assert await account.balances() == balances


@pytest.mark.parametrize(
    "kyc_data",
    [
        {"type": "individual"},
        {"type": "entity"},
        {"payload_version": 1},
        {"type": "individual", "payload_version": "1"},
    ],
)
async def test_create_an_account_with_invalid_kyc_data(target_client: RestClient, kyc_data: Dict[str, Any]) -> None:
    with pytest.raises(aiohttp.ClientResponseError, match="400") as einfo:
        await target_client.create("/accounts", kyc_data=kyc_data)

    assert "'kyc_data' must be JSON-encoded KycDataObject" in einfo.value.message


async def test_create_an_account_with_invalid_json_body(target_client: RestClient) -> None:
    with pytest.raises(aiohttp.ClientResponseError, match="400") as einfo:
        await target_client.send("POST", "/accounts", data="invalid json")

    assert "invalid JSON" in einfo.value.message


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
async def test_create_an_account_with_invalid_initial_deposit_balance_currency(
    target_client: RestClient, balances: str, err_msg
) -> None:
    with pytest.raises(aiohttp.ClientResponseError, match="400") as einfo:
        await target_client.create("/accounts", balances=json.loads(balances))

    assert err_msg in einfo.value.message


async def test_receive_multiple_payments(target_client: RestClient, stub_client: RestClient, currency: str) -> None:
    receiver = await stub_client.create_account()
    receiver_account_identifier = await receiver.generate_account_identifier()

    index = len(await receiver.events())
    amount = 1234
    sender1 = await target_client.create_account({currency: amount})
    await sender1.send_payment(currency, amount, receiver_account_identifier)

    sender2 = await target_client.create_account({currency: amount})
    await sender2.send_payment(currency, amount, receiver_account_identifier)

    await wait_for_balance(sender1, currency, 0)
    await wait_for_balance(sender2, currency, 0)
    await wait_for_balance(receiver, currency, amount * 2)

    events = await receiver.events(index)
    new_events = [e for e in events if e.type != "info"]
    assert len(new_events) == 2
    assert new_events[0].type == "created_transaction"
    assert new_events[1].type == "created_transaction"


async def test_account_balance_validation_should_exclude_canceled_transactions(
    target_client: RestClient, stub_client: RestClient, currency: str, travel_rule_threshold: int
) -> None:
    amount = travel_rule_threshold
    receiver = await target_client.create_account()
    payee = await receiver.generate_account_identifier()
    sender = await stub_client.create_account({currency: amount})
    # payment should be rejected during offchain kyc data exchange
    payment = await sender.send_payment(currency, amount, payee=payee)

    await wait_for_event(sender, "updated_transaction", id=payment.id, status="canceled")

    await sender.send_payment(currency, travel_rule_threshold - 1, payee)

    await wait_for_balance(receiver, currency, travel_rule_threshold - 1)
    await wait_for_balance(sender, currency, 1)


async def test_create_account_event(target_client: RestClient, currency: str) -> None:
    before_timestamp = int(time.time() * 1000)
    account = await target_client.create_account()
    after_timestamp = int(time.time() * 1000)

    events = await account.events()
    assert len(events) >= 1
    event = events[0]
    assert event.id
    assert event.timestamp >= before_timestamp
    assert event.timestamp <= after_timestamp
    assert event.type == "created_account"
    event_data = Account(**json.loads(event.data))
    assert event_data.kyc_data == account.kyc_data
    assert event_data.id == account.id


async def test_create_account_identifier_events(target_client: RestClient) -> None:
    account = await target_client.create_account()
    index = len(await account.events())
    ret = await account.generate_account_identifier()
    assert ret
    assert len(await account.events(index)) == 1
    events = await account.events(index)
    assert events[0].type == "created_subaddress"


async def test_openapi_spec(target_client: RestClient) -> None:
    text = await target_client.send("GET", "/openapi.yaml", return_text=True)
    assert text


async def test_generate_account_payment_URI_should_include_unique_subaddress(
    target_client: RestClient, hrp: str
) -> None:
    account = await target_client.create_account()

    def subaddress(account_identifier: str) -> str:
        return utils.hex(identifier.decode_account_subaddress(account_identifier, hrp))

    subaddresses = [subaddress(await account.generate_account_identifier()) for _ in range(10)]
    assert sorted(subaddresses) == sorted(list(set(subaddresses)))
