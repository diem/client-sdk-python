# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from libra import (
    auth_key,
    libra_types,
    utils,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import dataclasses


@dataclasses.dataclass
class LocalAccount:
    @staticmethod
    def gen() -> "LocalAccount":
        private_key = Ed25519PrivateKey.generate()
        return LocalAccount(
            private_key=private_key,
            authkey=auth_key.create_from_public_key(private_key.public_key()),
        )

    private_key: Ed25519PrivateKey
    authkey: auth_key.AuthKey

    def account_address(self) -> libra_types.AccountAddress:
        return self.authkey.account_address()

    def public_key(self) -> bytes:
        return utils.public_key_bytes(self.private_key.public_key())
