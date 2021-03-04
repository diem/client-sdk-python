# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.testing.miniwallet import RestClient
import pytest, requests, json


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
