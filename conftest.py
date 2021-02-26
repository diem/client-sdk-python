# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import chain_ids, testnet
import pytest, os


@pytest.fixture(scope="session", autouse=True)
def setup_testnet() -> None:
    if os.getenv("dt"):
        os.system("make docker")
        print("swap testnet default values to local testnet launched by docker-compose")
        testnet.JSON_RPC_URL = "http://localhost:8080/v1"
        testnet.FAUCET_URL = "http://localhost:8000/mint"
        testnet.CHAIN_ID = chain_ids.TESTING
