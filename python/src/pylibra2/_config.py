ASSOC_ADDRESS: str = "0000000000000000000000000a550c18"
ASSOC_AUTHKEY: str = "254d77ec7ceae382e842dcff2df1590753b260f98a749dbc77e307a15ae781a6"

TREASURY_ADDRESS: str = "0000000000000000000000000b1e55ed"

DESIGNATED_DEALER_ADDRESS: str = "000000000000000000000000000000dd"

CORE_CODE_ADDRESS: str = "00000000000000000000000000000001"

# Maximum time to iterate waiting for successful reasponse for mint & wait tx
MAX_WAIT_ITERATIONS: int = 10

# Time to sleep b/w checking the tx status
WAIT_TIME_FOR_TX_STATUS_CHECK: int = 1  # seconds

LIBRA_ADDRESS_LEN: int = 16  # units: bytes
LIBRA_PRIVATE_KEY_SIZE: int = 32  # units: bytes
LIBRA_EVENT_KEY_LEN: int = LIBRA_ADDRESS_LEN + 8  # units: bytes
LIBRA_HASH_PREFIX: bytes = b"LIBRA::"

# Status code for successful execution of tx in Libra Blockchain
LIBRA_VM_STATUS_EXECUTED = 4001

DEFAULT_JSON_RPC_SERVER: str = "https://client.testnet.libra.org/"
DEFAULT_FAUCET_SERVER: str = "http://faucet.testnet.libra.org"

# testnet
DEFAULT_LIBRA_CHAIN_ID: int = 2

# Field names in json-rpc response
# ref: https://github.com/thefallentree/libra/blob/master/json-rpc/types/src/views.rs#L29
JSONRPC_LIBRA_CHAIN_ID: str = "libra_chain_id"
JSONRPC_LIBRA_LEDGER_VERSION: str = "libra_ledger_version"
JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: str = "libra_ledger_timestampusec"
