# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

# pyre-strict
import typing

NETWORK_TESTNET: str = "testnet"
NETWORK_DEV: str = "dev"

NETWORK_DEFAULT: str = NETWORK_TESTNET

ENDPOINT_CONFIG: typing.Dict[str, typing.Dict[str, str]] = {
    NETWORK_TESTNET: {"json-rpc": "https://testnet.libra.org/v1", "faucet": "http://testnet.libra.org/mint"},
    NETWORK_DEV: {
        "json-rpc": "http://client.dev.aws.hlw3truzy4ls.com/",
        "faucet": "http://faucet.dev.aws.hlw3truzy4ls.com",
    },
}

# Default timeout value for requests
DEFAULT_CONNECT_TIMEOUT_SECS: float = 5.0
DEFAULT_TIMEOUT_SECS: float = 30.0

CHAIN_ID_MAINNET: int = 0
CHAIN_ID_PREMAINNET: int = 1
CHAIN_ID_TESTNET: int = 2
CHAIN_ID_DEVNET: int = 3
CHAIN_ID_TESTING: int = 4
