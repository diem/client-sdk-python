# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from ... import testnet
from ..miniwallet import RestClient, AppConfig
from .clients import Clients
from .envs import target_url, is_self_check, should_test_debug_api
import pytest


@pytest.fixture(scope="package")
def stub_config() -> AppConfig:
    return AppConfig(name="stub-wallet", enable_debug_api=True)


@pytest.fixture(scope="package")
def clients(stub_config: AppConfig) -> Clients:
    print("Diem JSON-RPC URL: %s" % testnet.JSON_RPC_URL)
    print("Diem Testnet Faucet URL: %s" % testnet.FAUCET_URL)
    print("Start stub app with config %s" % stub_config)
    diem_client = testnet.create_client()
    stub_config.start(diem_client)

    if is_self_check():
        conf = AppConfig(name="target-wallet", enable_debug_api=should_test_debug_api())
        print("self-checking, launch target app with config %s" % conf)
        conf.start(diem_client)
        target_client = conf.create_client()
    else:
        print("target wallet server url: %s" % target_url())
        target_client = RestClient(name="target-wallet-client", server_url=target_url()).with_retry()

    return Clients(
        target=target_client,
        stub=stub_config.create_client(),
        diem=diem_client,
    )


@pytest.fixture(scope="package")
def target_client(clients: Clients) -> RestClient:
    return clients.target


@pytest.fixture
def hrp() -> str:
    return testnet.HRP


@pytest.fixture
def currency() -> str:
    return testnet.TEST_CURRENCY_CODE


@pytest.fixture
def travel_rule_threshold(clients: Clients) -> int:
    # todo: convert the limit base on currency
    return clients.diem.get_metadata().dual_attestation_limit
