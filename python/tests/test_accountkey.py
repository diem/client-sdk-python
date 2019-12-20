# pyre-strict

import pytest
from pylibra import AccountKey


def test_invalid() -> None:
    with pytest.raises(ValueError):
        AccountKey(b"deadbeef")


def test_valid() -> None:
    private_key_bytes = bytes.fromhex("82001573a003fd3b7fd72ffb0eaf63aac62f12deb629dca72785a66268ec758b")
    public_key_bytes = bytes.fromhex("664f6e8f36eacb1770fa879d86c2c1d0fafea145e84fa7d671ab7a011a54d509")
    addr_bytes = bytes.fromhex("dde866d21d22926429919efe44436af450c69e62826119143baad55bb0319403")
    ak = AccountKey(private_key_bytes)
    assert ak.private_key == private_key_bytes
    assert ak.address == addr_bytes
    assert ak.public_key == public_key_bytes
