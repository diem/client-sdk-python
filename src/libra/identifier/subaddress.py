# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import secrets

LIBRA_SUBADDRESS_SIZE: int = 8  # in bytes (for V1)
LIBRA_ZERO_SUBADDRESS: bytes = b"\0" * LIBRA_SUBADDRESS_SIZE


def gen_subaddress() -> bytes:
    return secrets.token_bytes(LIBRA_SUBADDRESS_SIZE)
