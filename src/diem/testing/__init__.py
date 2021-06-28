# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module provides testing utilities:

1. MiniWallet application as counterparty wallet application stub for testing your wallet application.
2. Payment test suites provide tests running on top of MiniWallet API for testing wallet application payment features.
3. `LocalAccount` for managing local account keys and generating random local account.
4. Testnet Faucet service client
5. Testnet constants
"""

from diem.jsonrpc import AsyncClient
from diem.testing.constants import FAUCET_URL, JSON_RPC_URL, DD_ADDRESS, XUS
from diem.testing.faucet import Faucet
from diem.testing.local_account import LocalAccount

import os


def create_client() -> AsyncClient:
    """Create an `AsyncClient` initialized with Testnet JSON-RPC URL"""

    return AsyncClient(os.getenv("DIEM_JSON_RPC_URL") or JSON_RPC_URL)
