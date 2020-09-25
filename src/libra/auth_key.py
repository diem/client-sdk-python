# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import dataclasses
import typing

from . import utils, libra_types


def create_from_public_key(public_key: Ed25519PublicKey) -> "AuthKey":
    single_key_scheme = b"\x00"
    return AuthKey(utils.hash(utils.public_key_bytes(public_key), single_key_scheme))


@dataclasses.dataclass
class AuthKey:
    data: bytes

    def account_address(self) -> libra_types.AccountAddress:
        return utils.account_address(self.data[-utils.ACCOUNT_ADDRESS_LEN :])

    def prefix(self) -> bytes:
        return self.data[-utils.ACCOUNT_ADDRESS_LEN :]

    def hex(self) -> str:
        return self.data.hex()
