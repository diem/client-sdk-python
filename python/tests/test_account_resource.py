# pyre-strict

import pytest
import os
from pylibra import AccountResource

ASSOC_ACCOUNTSTATE_BYTES: bytes

# Generate file by using cli
# > q as 000000000000000000000000000000000000000000000000000000000a550c18
base_dir: str = os.path.dirname(os.path.realpath(__file__))
with open(base_dir + "/assoc_asblob.txt", "rb") as f:
    ASSOC_ACCOUNTSTATE_BYTES = bytes.fromhex(f.readlines()[0].decode("utf8"))

# These should not change
TEST_ADDR_BYTES: bytes = bytes.fromhex("deadbeef" * 8)
ASSOC_AUTHKEY_BYTES: bytes = (
    b"3\xf8\xa4\xea\xa19\x9b\x15\x81\xb2pW)\xd2\xed%\xde!\xb9 \tyS\xba*\x88\xf3\x19\xb6\x98<\xb3"
)
ASSOC_ADDR_BYTES: bytes = bytes.fromhex("000000000000000000000000000000000000000000000000000000000a550c18")


def test_account_state_blob_invalid() -> None:
    with pytest.raises(ValueError):
        assert AccountResource.create(TEST_ADDR_BYTES, b"deadbeef")


def test_account_state_blob_assoc() -> None:
    ar = AccountResource.create(ASSOC_ADDR_BYTES, ASSOC_ACCOUNTSTATE_BYTES)
    assert ar.address == ASSOC_ADDR_BYTES
    assert ar.balance == 1000001028000000
    assert ar.sequence == 8694
    assert ar.authentication_key == ASSOC_AUTHKEY_BYTES
    assert ar.delegated_key_rotation_capability is False
    assert ar.delegated_withdrawal_capability is False
    assert ar.sent_events.count == 8498
    assert ar.sent_events.key == b"\x01\x00\x00\x00\x00\x00\x00\x00" + ASSOC_ADDR_BYTES
    assert ar.received_events.count == 91
    assert ar.received_events.key == b"\x00\x00\x00\x00\x00\x00\x00\x00" + ASSOC_ADDR_BYTES
