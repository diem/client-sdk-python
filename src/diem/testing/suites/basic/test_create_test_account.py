# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain
from diem.testing.miniwallet import RestClient
import pytest


pytestmark = pytest.mark.asyncio  # pyre-ignore


async def test_create_a_blank_account(target_client: RestClient) -> None:
    account = await target_client.create_account()
    assert account.id
    assert await account.balance("XUS") == 0
    assert await account.balance("XDX") == 0


@pytest.mark.parametrize("amount", [0, 1, 100, 10000000000])
@pytest.mark.parametrize("currency", ["XUS"])
async def test_create_an_account_with_initial_deposit_balances(
    target_client: RestClient, currency: str, amount: int
) -> None:
    account = await target_client.create_account(kyc_data=None, balances={currency: amount})
    assert account.id
    assert await account.balance(currency) == amount


@pytest.mark.parametrize(  # pyre-ignore
    "kyc_data",
    [
        offchain.individual_kyc_data(),
        offchain.entity_kyc_data(),
    ],
)
async def test_create_an_account_with_minimum_valid_kyc_data(
    target_client: RestClient, kyc_data: offchain.KycDataObject
) -> None:
    account = await target_client.create_account(kyc_data=kyc_data)
    assert account.id


async def test_create_an_account_with_valid_kyc_data_and_initial_deposit_balances(
    target_client: RestClient, currency: str
) -> None:
    minimum_kyc_data = offchain.individual_kyc_data()
    account = await target_client.create_account(kyc_data=minimum_kyc_data, balances={currency: 123})
    assert account.id


async def test_account_id_should_be_unique(target_client: RestClient) -> None:
    ids = []
    for _ in range(10):
        account = await target_client.create_account()
        ids.append(account.id)
    assert sorted(ids) == sorted(list(set(ids)))
