# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Python client SDK library for the [Diem](https://diem.com) blockchain network."""

from .constants import (
    ACCOUNT_ADDRESS_LEN,
    SUB_ADDRESS_LEN,
    DIEM_HASH_PREFIX,
    ROOT_ADDRESS,
    TREASURY_ADDRESS,
    CORE_CODE_ADDRESS,
)

from .utils import InvalidAccountAddressError, InvalidSubAddressError
from .auth_key import AuthKey

# keep this import for backwards compatible
from .testing import LocalAccount
