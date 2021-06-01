# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import jsonrpc, testnet
from diem.testing.miniwallet import RestClient, AppConfig
import pytest


@pytest.fixture(scope="package")
def target_client(diem_client: jsonrpc.Client) -> RestClient:
    return start_app(diem_client, "targetwallet").create_client()


@pytest.fixture(scope="package")
def stub_client(diem_client: jsonrpc.Client) -> RestClient:
    return start_app(diem_client, "stubwallet").create_client()


@pytest.fixture(scope="package")
def diem_client() -> jsonrpc.Client:
    return testnet.create_client()


@pytest.fixture
def hrp() -> str:
    return testnet.HRP


@pytest.fixture
def currency() -> str:
    return testnet.TEST_CURRENCY_CODE


@pytest.fixture
def travel_rule_threshold(diem_client: jsonrpc.Client) -> int:
    return diem_client.get_metadata().dual_attestation_limit


def start_app(diem_client: jsonrpc.Client, app_name: str) -> AppConfig:
    conf = AppConfig(name=app_name, diem_id_domain=app_name)
    print("launch %s with config %s" % (app_name, conf))
    conf.start(diem_client)
    return conf
