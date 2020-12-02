# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Provides AuthKey class for holding Diem authentication key and generating account address, prefix from it."""

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from . import utils, diem_types


class AuthKey:
    """Diem Authentication Key

    Wraps authentication key bytes, derives account address and authentication key prefix.
    """

    data: bytes

    @staticmethod
    def from_public_key(public_key: Ed25519PublicKey) -> "AuthKey":
        single_key_scheme = b"\x00"
        return AuthKey(utils.hash(utils.public_key_bytes(public_key), single_key_scheme))

    def __init__(self, data: bytes) -> None:
        self.data = data

    def account_address(self) -> diem_types.AccountAddress:
        return utils.account_address(self.data[-utils.ACCOUNT_ADDRESS_LEN :])

    def prefix(self) -> bytes:
        return self.data[: -utils.ACCOUNT_ADDRESS_LEN]

    def hex(self) -> str:
        return self.data.hex()
