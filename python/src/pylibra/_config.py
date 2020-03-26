# pyre-strict
import typing

NETWORK_TESTNET: str = "testnet"
NETWORK_DEV: str = "dev"

NETWORK_DEFAULT: str = NETWORK_TESTNET

ENDPOINT_CONFIG: typing.Dict[str, typing.Dict[str, str]] = {
    NETWORK_TESTNET: {"json-rpc": "https://client.testnet.libra.org/", "faucet": "http://faucet.testnet.libra.org"},
    NETWORK_DEV: {
        "json-rpc": "http://client.dev.aws.hlw3truzy4ls.com/",
        "faucet": "http://faucet.dev.aws.hlw3truzy4ls.com",
    },
}
