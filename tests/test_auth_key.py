# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from diem import AuthKey


def test_new_auth_key_from_public_key():
    key_bytes = bytes.fromhex("447fc3be296803c2303951c7816624c7566730a5cc6860a4a1bd3c04731569f5")
    public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
    auth_key = AuthKey.from_public_key(public_key)
    assert auth_key.hex() == "459c77a38803bd53f3adee52703810e3a74fd7c46952c497e75afb0a7932586d"
    assert auth_key.prefix().hex() == "459c77a38803bd53f3adee52703810e3"
    assert auth_key.account_address().to_hex() == "a74fd7c46952c497e75afb0a7932586d"
