# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Defines constants for enum type values

See the following Diem JSON-RPC response type documents for more details:

* https://github.com/diem/diem/blob/master/json-rpc/docs/type_account.md#type-account
* https://github.com/diem/diem/blob/master/json-rpc/docs/type_event.md#event-data
* https://github.com/diem/diem/blob/master/json-rpc/docs/type_transaction.md#type-vmstatus
* https://github.com/diem/diem/blob/master/json-rpc/docs/type_transaction.md#type-transactiondata


"""

# AccountRole#type field values
ACCOUNT_ROLE_UNKNOWN: str = "unknown"
ACCOUNT_ROLE_CHILD_VASP: str = "child_vasp"
ACCOUNT_ROLE_PARENT_VASP: str = "parent_vasp"
ACCOUNT_ROLE_DESIGNATED_DEALER: str = "designated_dealer"


# EventData#type field values
EVENT_DATA_UNKNOWN: str = "unknown"
EVENT_DATA_BURN: str = "burn"
EVENT_DATA_CANCEL_BURN: str = "cancelburn"
EVENT_DATA_MINT: str = "mint"
EVENT_DATA_TO_XDX_EXCHANGE_RATE_UPDATE: str = "to_xdx_exchange_rate_update"
EVENT_DATA_PREBURN: str = "preburn"
EVENT_DATA_RECEIVED_PAYMENT: str = "receivedpayment"
EVENT_DATA_SENT_PAYMENT: str = "sentpayment"
EVENT_DATA_NEW_EPOCH: str = "newepoch"
EVENT_DATA_NEW_BLOCK: str = "newblock"
EVENT_DATA_RECEIVED_MINT: str = "receivedmint"
EVENT_DATA_COMPLIANCE_KEY_ROTATION: str = "compliancekeyrotation"
EVENT_DATA_BASE_URL_ROTATION: str = "baseurlrotation"
EVENT_DATA_CREATE_ACCOUNT: str = "createaccount"
EVENT_DATA_ADMIN_TRANSACTION: str = "admintransaction"


# VMStatus#type field values
VM_STATUS_EXECUTED: str = "executed"
VM_STATUS_OUT_OF_GAS: str = "out_of_gas"
VM_STATUS_MOVE_ABORT: str = "move_abort"
VM_STATUS_EXECUTION_FAILURE: str = "execution_failure"
VM_STATUS_MISC_ERROR: str = "miscellaneous_error"


# TransactionData#type field values
TRANSACTION_DATA_BLOCK_METADATA: str = "blockmetadata"
TRANSACTION_DATA_WRITE_SET: str = "writeset"
TRANSACTION_DATA_USER: str = "user"
TRANSACTION_DATA_UNKNOWN: str = "unknown"


# Script#type field values, only set unknown type here,
# other types, plese see https://github.com/diem/diem/blob/master/language/stdlib/transaction_scripts/doc/transaction_script_documentation.md for all available script names.
SCRIPT_UNKNOWN: str = "unknown"
