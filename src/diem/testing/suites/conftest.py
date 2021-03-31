# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from ... import testnet, jsonrpc
from ..miniwallet import RestClient, AppConfig, AccountResource, ServerConfig
from ..miniwallet.app.event_puller import PENDING_INBOUND_ACCOUNT_ID
from .envs import (
    target_url,
    is_self_check,
    should_test_debug_api,
    dmw_stub_server,
    dmw_stub_diem_account_config,
)
import pytest, json


@pytest.fixture(scope="package")
def target_client(diem_client: jsonrpc.Client) -> RestClient:
    if is_self_check():
        conf = AppConfig(name="target-wallet", enable_debug_api=should_test_debug_api())
        print("self-checking, launch target app with config %s" % conf)
        conf.start(diem_client)
        return conf.create_client()
    print("target wallet server url: %s" % target_url())
    return RestClient(name="target-wallet-client", server_url=target_url()).with_retry()


@pytest.fixture(scope="package")
def diem_client() -> jsonrpc.Client:
    print("Diem JSON-RPC URL: %s" % testnet.JSON_RPC_URL)
    print("Diem Testnet Faucet URL: %s" % testnet.FAUCET_URL)
    return testnet.create_client()


@pytest.fixture(scope="package")
def stub_config() -> AppConfig:
    conf = AppConfig(name="stub-wallet", enable_debug_api=True, server_conf=ServerConfig(**dmw_stub_server()))
    account_conf = dmw_stub_diem_account_config()
    if account_conf:
        print("loads stub account config: %s" % account_conf)
        conf.account_config = json.loads(account_conf)
    return conf


@pytest.fixture(scope="package")
def stub_client(stub_config: AppConfig, diem_client: jsonrpc.Client) -> RestClient:
    print("Start stub app with config %s" % stub_config)
    stub_config.start(diem_client)
    return stub_config.create_client()


@pytest.fixture
def hrp(stub_config: AppConfig) -> str:
    return stub_config.account.hrp


@pytest.fixture
def currency() -> str:
    return testnet.TEST_CURRENCY_CODE


@pytest.fixture
def travel_rule_threshold(diem_client: jsonrpc.Client) -> int:
    # todo: convert the limit base on currency
    return diem_client.get_metadata().dual_attestation_limit


@pytest.fixture
def pending_income_account(stub_client: RestClient) -> AccountResource:
    return AccountResource(id=PENDING_INBOUND_ACCOUNT_ID, client=stub_client)
