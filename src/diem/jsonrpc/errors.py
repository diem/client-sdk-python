# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from .jsonrpc_pb2 import Transaction
from .state import State


class JsonRpcError(Exception):
    pass


class NetworkError(Exception):
    pass


class InvalidServerResponse(Exception):
    pass


class StaleResponseError(Exception):
    pass


class TransactionHashMismatchError(Exception):
    def __init__(self, txn: Transaction, expected_hash: str) -> None:
        self.txn = txn
        self.expected_hash = expected_hash


class TransactionExecutionFailed(Exception):
    def __init__(self, txn: Transaction) -> None:
        self.txn = txn


class TransactionExpired(Exception):
    def __init__(self, state: State, expected_expiration_time_secs: int) -> None:
        self.state = state
        self.expected_expiration_time_secs = expected_expiration_time_secs


class WaitForTransactionTimeout(Exception):
    def __init__(self, start_time: float, end_time: float) -> None:
        self.start_time = start_time
        self.end_time = end_time


class AccountNotFoundError(ValueError):
    pass
