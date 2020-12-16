# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Provides LocalAccount class for holding local account private key.

LocalAccount provides operations we need for creating auth key, account address and signing
raw transaction.
"""

from . import (
    diem_types,
    utils,
)

from .auth_key import AuthKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class LocalAccount:
    """LocalAccount is like a wallet account

    WARN: This is handy class for creating tests for your application, but may not ideal for your
    production code, because it uses a specific implementaion of ed25519 and requires loading your
    private key into memory and hand over to code from external.
    You should always choose more secure way to handle your private key
    (e.g. https://en.wikipedia.org/wiki/Hardware_security_module) in production and do not give
    your private key to any code from external if possible.
    """

    @staticmethod
    def generate() -> "LocalAccount":
        """Generate a random private key and initialize local account"""

        private_key = Ed25519PrivateKey.generate()
        return LocalAccount(private_key)

    @staticmethod
    def from_private_key_hex(key: str) -> "LocalAccount":
        return LocalAccount(Ed25519PrivateKey.from_private_bytes(bytes.fromhex(key)))

    private_key: Ed25519PrivateKey
    compliance_key: Ed25519PrivateKey

    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self.private_key = private_key
        self.compliance_key = Ed25519PrivateKey.generate()

    @property
    def auth_key(self) -> AuthKey:
        return AuthKey.from_public_key(self.public_key)

    @property
    def account_address(self) -> diem_types.AccountAddress:
        return self.auth_key.account_address()

    @property
    def public_key_bytes(self) -> bytes:
        return utils.public_key_bytes(self.public_key)

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self.private_key.public_key()

    @property
    def compliance_public_key_bytes(self) -> bytes:
        return utils.public_key_bytes(self.compliance_key.public_key())

    def sign(self, txn: diem_types.RawTransaction) -> diem_types.SignedTransaction:
        """Create signed transaction for given raw transaction"""

        signature = self.private_key.sign(utils.raw_transaction_signing_msg(txn))
        return utils.create_signed_transaction(txn, self.public_key_bytes, signature)
