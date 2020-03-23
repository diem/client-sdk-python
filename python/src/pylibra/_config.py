# pyre-strict

NETWORK_TESTNET = "testnet"
NETWORK_DEV = "dev"

NETWORK_DEFAULT = NETWORK_TESTNET

ENDPOINT_CONFIG = {
    NETWORK_TESTNET: {"json-rpc": "https://client.testnet.libra.org/", "faucet": "http://faucet.testnet.libra.org"},
    NETWORK_DEV: {
        "json-rpc": "http://client.dev.aws.hlw3truzy4ls.com/",
        "faucet": "http://faucet.dev.aws.hlw3truzy4ls.com",
    },
}
