# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module provides testing utilities:

1. MiniWallet application as counterparty wallet application stub for testing your wallet application.
2. Payment test suites provide tests running on top of MiniWallet API for testing wallet application payment features.
3. `LocalAccount` for managing local account keys and generating random local account.
"""

from .local_account import LocalAccount
