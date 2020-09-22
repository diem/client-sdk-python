ASSOC_ADDRESS: str = "0000000000000000000000000a550c18"

TREASURY_ADDRESS: str = "0000000000000000000000000b1e55ed"

DESIGNATED_DEALER_ADDRESS: str = "000000000000000000000000000000dd"

CORE_CODE_ADDRESS: str = "00000000000000000000000000000001"

# Maximum time to iterate waiting for successful reasponse for mint & wait tx
MAX_WAIT_ITERATIONS: int = 10

# Time to sleep b/w checking the tx status
WAIT_TIME_FOR_TX_STATUS_CHECK: int = 1  # seconds

LIBRA_ADDRESS_LEN: int = 16  # units: bytes
LIBRA_PRIVATE_KEY_SIZE: int = 32  # units: bytes
LIBRA_AUTH_KEY_SIZE: int = 32  # units: bytes
LIBRA_EVENT_KEY_LEN: int = LIBRA_ADDRESS_LEN + 8  # units: bytes
LIBRA_HASH_PREFIX: bytes = b"LIBRA::"

# Status response for successful execution of tx in Libra Blockchain
LIBRA_VM_STATUS_EXECUTED = "executed"

DEFAULT_JSON_RPC_SERVER: str = "https://testnet.libra.org/v1"
DEFAULT_FAUCET_SERVER: str = "https://testnet.libra.org/mint"

# http request - connection timeout & normal timeout duration
DEFAULT_CONNECT_TIMEOUT_SECS: float = 5.0
DEFAULT_TIMEOUT_SECS: float = 30.0

# testnet
DEFAULT_LIBRA_CHAIN_ID: int = 2


# Field names in json-rpc response
# ref: https://github.com/thefallentree/libra/blob/master/json-rpc/types/src/views.rs#L29
JSONRPC_LIBRA_CHAIN_ID: str = "libra_chain_id"
JSONRPC_LIBRA_LEDGER_VERSION: str = "libra_ledger_version"
JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: str = "libra_ledger_timestampusec"

# Name constants for event types
SENT_PAYMENT_TYPE = "sentpayment"
RECEIVED_PAYMENT_TYPE = "receivedpayment"
UNKNOWN_EVENT_TYPE = "unknown"
