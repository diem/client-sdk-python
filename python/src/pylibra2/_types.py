from dataclasses import dataclass
from enum import Enum, IntEnum


class SubmitTransactionError(Exception):
    pass


class TxStatus(Enum):
    SUCCESS = 1
    EXPIRED = 2
    EXECUTION_FAIL = 3
    FETCH_STATUS_FAIL = 4
    UNKNOWN = 5


class ChainId(IntEnum):
    MAINNET = 0
    PREMAINNET = 1
    TESTNET = 2
    DEVNET = 3
    TESTING = 4


@dataclass
class LibraLedgerState:
    chain_id: int
    blockchain_version: int
    blockchain_timestamp_usecs: int
