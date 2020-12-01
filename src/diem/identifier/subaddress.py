# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import secrets

DIEM_SUBADDRESS_SIZE: int = 8  # in bytes (for V1)
DIEM_ZERO_SUBADDRESS: bytes = b"\0" * DIEM_SUBADDRESS_SIZE


def gen_subaddress() -> bytes:
    return secrets.token_bytes(DIEM_SUBADDRESS_SIZE)
