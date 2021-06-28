# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


class JsonRpcError(Exception):
    pass


class NetworkError(Exception):
    pass


class InvalidServerResponse(Exception):
    pass


class StaleResponseError(Exception):
    pass


class TransactionHashMismatchError(Exception):
    pass


class TransactionExecutionFailed(Exception):
    pass


class TransactionExpired(Exception):
    pass


class WaitForTransactionTimeout(Exception):
    pass


class AccountNotFoundError(ValueError):
    pass
