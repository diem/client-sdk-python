# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem.testing.miniwallet import RestClient, AccountResource
from diem import identifier, utils
from typing import Union
import pytest, requests


@pytest.fixture
def account(target_client: RestClient) -> AccountResource:
    return target_client.create_account()


def test_generate_account_payment_uri_without_currency_and_amount(account: AccountResource, hrp: str) -> None:
    uri = account.generate_payment_uri()
    assert uri.id
    assert uri.account_id == account.id
    assert uri.payment_uri

    intent = identifier.decode_intent(uri.payment_uri, hrp)
    assert intent.account_address
    assert intent.subaddress
    assert intent.currency_code is None
    assert intent.amount is None


def test_generate_account_payment_uri_with_currency(account: AccountResource, currency: str, hrp: str) -> None:
    uri = account.generate_payment_uri(currency=currency)
    assert uri.id
    assert uri.account_id == account.id

    intent = identifier.decode_intent(uri.payment_uri, hrp)
    assert intent.account_address
    assert intent.subaddress
    assert intent.currency_code == currency
    assert intent.amount is None


def test_generate_account_payment_uri_with_amount(account: AccountResource, hrp: str) -> None:
    amount = 1123
    uri = account.generate_payment_uri(amount=amount)
    assert uri.id
    assert uri.account_id == account.id

    intent = identifier.decode_intent(uri.payment_uri, hrp)
    assert intent.account_address
    assert intent.subaddress
    assert intent.currency_code is None
    assert intent.amount == amount


def test_generate_account_payment_uri_with_currency_and_amount(
    account: AccountResource, currency: str, hrp: str
) -> None:
    amount = 1123
    uri = account.generate_payment_uri(currency=currency, amount=amount)
    assert uri.id
    assert uri.account_id == account.id

    intent = identifier.decode_intent(uri.payment_uri, hrp)
    assert intent.account_address
    assert intent.subaddress
    assert intent.currency_code == currency
    assert intent.amount == amount


@pytest.mark.parametrize("invalid_currency", ["XU", "USD", "xus", "", '"XUS"', "X"])
def test_generate_account_payment_uri_with_invalid_currency(account: AccountResource, invalid_currency: str) -> None:
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        account.generate_payment_uri(currency=invalid_currency)


@pytest.mark.parametrize("amount", ["123", 12.34, -1, ""])
def test_generate_account_payment_uri_with_invalid_amount(account: AccountResource, amount: Union[str, int]) -> None:
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        account.generate_payment_uri(amount=amount)  # pyre-ignore


def test_generate_account_payment_uri_with_integer_overflow_amount(account: AccountResource) -> None:
    amount = 324234324342234234234234242234234324323423432432423423243242342342342342342342342334234
    with pytest.raises(requests.HTTPError, match="400 Client Error"):
        account.generate_payment_uri(amount=amount)


def test_generate_account_payment_URI_should_include_unique_subaddress(account: AccountResource, hrp: str) -> None:
    def subaddress(uri: str) -> str:
        return utils.hex(identifier.decode_intent(uri, hrp).subaddress)

    subaddresses = [subaddress(account.generate_payment_uri().payment_uri) for _ in range(10)]
    assert sorted(subaddresses) == sorted(list(set(subaddresses)))
