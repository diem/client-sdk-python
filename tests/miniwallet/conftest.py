# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import jsonrpc, testnet
from diem.testing.miniwallet import RestClient, AppConfig
import pytest


@pytest.fixture(scope="package")
def target_client(diem_client: jsonrpc.Client) -> RestClient:
    conf = AppConfig(name="target-wallet")
    print("launch target app with config %s" % conf)
    conf.start(diem_client)
    return conf.create_client()


@pytest.fixture(scope="package")
def diem_client() -> jsonrpc.Client:
    return testnet.create_client()
