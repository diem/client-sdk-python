# pyre-strict

import pytest
from pylibra import AccountResource

TEST_ADDR_BYTES: bytes = bytes.fromhex("deadbeef" * 8)


def test_account_state_blob_invalid() -> None:
    with pytest.raises(ValueError):
        assert AccountResource.create(TEST_ADDR_BYTES, b"deadbeef")


def test_account_state_blob_empty() -> None:
    ar = AccountResource.create(TEST_ADDR_BYTES, b"")
    assert ar.address == TEST_ADDR_BYTES
    assert ar.balance == 0
    assert ar.sequence == 0
    assert ar.authentication_key == TEST_ADDR_BYTES
    assert ar.delegated_key_rotation_capability is False
    assert ar.delegated_withdrawal_capability is False
    assert ar.sent_events.count == 0
    assert ar.sent_events.key == bytes.fromhex("00" * 40)
    assert ar.received_events.count == 0
    assert ar.sent_events.key == bytes.fromhex("00" * 40)
