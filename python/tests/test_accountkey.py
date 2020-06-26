# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

# pyre-strict

import pytest
from pylibra import AccountKeyUtils


def test_invalid() -> None:
    with pytest.raises(ValueError):
        AccountKeyUtils.from_private_key(b"deadbeef")


def test_valid() -> None:
    private_key_bytes = bytes.fromhex("82001573a003fd3b7fd72ffb0eaf63aac62f12deb629dca72785a66268ec758b")
    public_key_bytes = bytes.fromhex("664f6e8f36eacb1770fa879d86c2c1d0fafea145e84fa7d671ab7a011a54d509")
    addr_hex = "0468de5bb622c235a681b898929cecf7"
    authkey_hex = "231a656a51c1792efdb10f42ddbca0f80468de5bb622c235a681b898929cecf7"
    ak = AccountKeyUtils.from_private_key(private_key_bytes)
    assert ak.private_key == private_key_bytes
    assert ak.public_key == public_key_bytes
    assert bytes.hex(ak.authentication_key) == authkey_hex
    assert bytes.hex(ak.address) == addr_hex
