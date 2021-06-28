# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import jsonrpc, testnet
from diem.testing.miniwallet import RestClient, AppConfig
from typing import Generator
import asyncio, pytest


@pytest.fixture(scope="package")
def event_loop() -> Generator[asyncio.events.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="package")
async def target_client(diem_client: jsonrpc.Client) -> RestClient:
    app = await start_app(diem_client, "target-wallet")
    print("start to create client")
    return app.create_client()


@pytest.fixture(scope="package")
async def stub_client(diem_client: jsonrpc.Client) -> RestClient:
    app = await start_app(diem_client, "stub-wallet")
    return app.create_client()


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
async def travel_rule_threshold(diem_client: jsonrpc.Client) -> int:
    metadata = await diem_client.get_metadata()
    return metadata.dual_attestation_limit


async def start_app(diem_client: jsonrpc.Client, app_name: str) -> AppConfig:
    conf = AppConfig(name=app_name)
    print("launch %s with config %s" % (app_name, conf))
    await conf.start(diem_client)
    return conf
