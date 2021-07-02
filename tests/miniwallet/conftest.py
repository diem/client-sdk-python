# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import identifier, utils
from diem.jsonrpc import AsyncClient
from diem.testing import create_client, XUS
from diem.testing.miniwallet import RestClient, AppConfig, App
from typing import Generator, Tuple, AsyncGenerator
import asyncio, pytest


@pytest.fixture(scope="package")
def event_loop() -> Generator[asyncio.events.AbstractEventLoop, None, None]:
    """Create a generator to yield an event_loop instance with graceful shutdown

    The logic is same with `asyncio.run`, except `yield` an event loop instance
    as pytest fixture.
    """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        utils.shutdown_event_loop(loop)


@pytest.fixture(scope="package")
async def target_client(diem_client: AsyncClient) -> RestClient:
    conf, app = await start_app(diem_client, "target-wallet")
    print("start to create client")
    return conf.create_client()


@pytest.fixture(scope="package")
async def stub_client(diem_client: AsyncClient) -> RestClient:
    conf, app = await start_app(diem_client, "stub-wallet")
    return conf.create_client()


@pytest.fixture(scope="package")
async def diem_client() -> AsyncGenerator[AsyncClient, None]:
    async with create_client() as client:
        yield client


@pytest.fixture
def hrp() -> str:
    return identifier.TDM


@pytest.fixture
def currency() -> str:
    return XUS


@pytest.fixture
async def travel_rule_threshold(diem_client: AsyncClient) -> int:
    metadata = await diem_client.get_metadata()
    return metadata.dual_attestation_limit


async def start_app(diem_client: AsyncClient, app_name: str) -> Tuple[AppConfig, App]:
    conf = AppConfig(name=app_name)
    print("launch %s with config %s" % (app_name, conf))
    app = await conf.start(diem_client)
    return (conf, app)
