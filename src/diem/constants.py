# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Diem constants"""

from diem import diem_types


ACCOUNT_ADDRESS_LEN: int = diem_types.AccountAddress.LENGTH
SUB_ADDRESS_LEN: int = 8
DIEM_HASH_PREFIX: bytes = b"DIEM::"
ROOT_ADDRESS: str = "0000000000000000000000000a550c18"
TREASURY_ADDRESS: str = "0000000000000000000000000b1e55ed"
CORE_CODE_ADDRESS: str = "00000000000000000000000000000001"
