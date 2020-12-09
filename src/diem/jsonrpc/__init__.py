# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

""" This package provides a client for connecting to Diem JSON-RPC Service API

Create a client connect to Diem Testnet and calls get_metadata API:

```python3

>>> from diem import jsonrpc, testnet
>>> client = jsonrpc.Client(testnet.JSON_RPC_URL)
>>> client.get_metadata()
version: 3300304
timestamp: 1601492912847973
chain_id: 2

```

See [Diem JSON-RPC API SPEC](https://github.com/diem/diem/blob/master/json-rpc/json-rpc-spec.md) for more details

"""

from .client import (
    Client,
    State,
    Retry,
    RequestStrategy,
    RequestWithBackups,
    # Exceptions
    JsonRpcError,
    NetworkError,
    InvalidServerResponse,
    StaleResponseError,
    TransactionHashMismatchError,
    TransactionExecutionFailed,
    TransactionExpired,
    WaitForTransactionTimeout,
    AccountNotFoundError,
)
from .jsonrpc_pb2 import (
    Amount,
    Metadata,
    CurrencyInfo,
    Account,
    AccountRole,
    Transaction,
    TransactionData,
    Script,
    Event,
    EventData,
    VMStatus,
    StateProof,
    AccountStateWithProof,
    AccountStateProof,
)
from .constants import (
    # AccountRole#type field values
    ACCOUNT_ROLE_UNKNOWN,
    ACCOUNT_ROLE_CHILD_VASP,
    ACCOUNT_ROLE_PARENT_VASP,
    ACCOUNT_ROLE_DESIGNATED_DEALER,
    # EventData#type field values
    EVENT_DATA_UNKNOWN,
    EVENT_DATA_BURN,
    EVENT_DATA_CANCEL_BURN,
    EVENT_DATA_MINT,
    EVENT_DATA_TO_XDX_EXCHANGE_RATE_UPDATE,
    EVENT_DATA_PREBURN,
    EVENT_DATA_RECEIVED_PAYMENT,
    EVENT_DATA_SENT_PAYMENT,
    EVENT_DATA_NEW_EPOCH,
    EVENT_DATA_NEW_BLOCK,
    EVENT_DATA_RECEIVED_MINT,
    EVENT_DATA_COMPLIANCE_KEY_ROTATION,
    EVENT_DATA_BASE_URL_ROTATION,
    EVENT_DATA_CREATE_ACCOUNT,
    EVENT_DATA_ADMIN_TRANSACTION,
    # VMStatus#type field values
    VM_STATUS_EXECUTED,
    VM_STATUS_OUT_OF_GAS,
    VM_STATUS_MOVE_ABORT,
    VM_STATUS_EXECUTION_FAILURE,
    VM_STATUS_MISC_ERROR,
    # TransactionData#type field values
    TRANSACTION_DATA_BLOCK_METADATA,
    TRANSACTION_DATA_WRITE_SET,
    TRANSACTION_DATA_USER,
    TRANSACTION_DATA_UNKNOWN,
    # Script#type field values, only set unknown type here,
    # other types, plese see https://github.com/diem/diem/blob/master/language/stdlib/transaction_scripts/doc/transaction_script_documentation.md for all available script names.
    SCRIPT_UNKNOWN,
)
