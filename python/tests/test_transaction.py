# pyre-strict

import pytest
from pylibra import TransactionUtils, AccountKeyUtils

RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 16)
RECEIVER_AUTHKEY_PREFIX: bytes = bytes.fromhex("00" * 16)
PRIVATE_KEY: bytes = bytes.fromhex("11" * 32)
PUBLIC_KEY: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).public_key
ADDRESS: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).address

SIGNED_TXN_BYTES_HEX: str = (
    "6dfcea9ac61f0a8420e5d01fbd8f0ea8ff0000000000000002f801a11ceb0b0100070146"
    "00000004000000034a00000011000000045b00000004000000055f000000180000000777"
    "0000005100000008c80000001000000009d8000000200000000000000101020001010101"
    "030203000104040101010006020602050a0200010501010305030a0204050a02030a0201"
    "0900063c53454c463e0c4c696272614163636f756e74176372656174655f756e686f7374"
    "65645f6163636f756e74066578697374731d7061795f66726f6d5f73656e6465725f7769"
    "74685f6d6574616461746100000000000000000000000000000000010105050d000a0011"
    "01200305000508000a000a013d000a000a020b033d010201060000000000000000000000"
    "0000000000034c4252015400040100000000000000000000000000000000021000000000"
    "00000000000000000000000000b168de3a0000000002086d65746164617461e022020000"
    "000000000000000000000015cd5b07000000000020d04ab232742bb4ab3a1368bd4615e4"
    "e6d0224ab71a016baf8520a332c9778737405b4b7bb1044162d9d0c312e6ab14ad951282"
    "7cf389d666f33c910aa0fbe6ee9370c1fba00f7c8ce69f1f7904cbe420579434de754751"
    "fde3d6a7fd764233b90e"
)

SIGNED_TXN_BYTES_WITHOUT_METADATA: str = (
    "6dfcea9ac61f0a8420e5d01fbd8f0ea8ff0000000000000002f801a11ceb0b0100070146"
    "00000004000000034a00000011000000045b00000004000000055f000000180000000777"
    "0000005100000008c80000001000000009d8000000200000000000000101020001010101"
    "030203000104040101010006020602050a0200010501010305030a0204050a02030a0201"
    "0900063c53454c463e0c4c696272614163636f756e74176372656174655f756e686f7374"
    "65645f6163636f756e74066578697374731d7061795f66726f6d5f73656e6465725f7769"
    "74685f6d6574616461746100000000000000000000000000000000010105050d000a0011"
    "01200305000508000a000a013d000a000a020b033d010201060000000000000000000000"
    "0000000000034c4252015400040100000000000000000000000000000000021000000000"
    "00000000000000000000000000b168de3a000000000200e0220200000000000000000000"
    "00000015cd5b07000000000020d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016b"
    "af8520a332c97787374078ffa5b9ace41f069e97e0cd49b6428ec84012c97bc307a135e9"
    "c0c6a691d228cd392d8d2c20ef41e8350ff549cc7b468d7ed9e0d9658c0f435014b5fb6e"
    "2602"
)

SIGNATURE_BYTES: bytes = bytes.fromhex(
    "5b4b7bb1044162d9d0c312e6ab14ad9512827cf389d666f33c910aa0fbe6ee9370c1fba0"
    "0f7c8ce69f1f7904cbe420579434de754751fde3d6a7fd764233b90e"
)

GAS_USED: int = 12


def test_sign_transaction() -> None:
    tx = TransactionUtils.createSignedP2PTransaction(
        PRIVATE_KEY,
        RECEIVER_ADDRESS,
        RECEIVER_AUTHKEY_PREFIX,
        # sequence
        255,
        # micro libra
        987_654_321,
        expiration_time=123_456_789,
        max_gas_amount=140000,
        metadata=b"metadata",
    )

    assert SIGNED_TXN_BYTES_HEX == bytes.hex(tx)


def test_sign_transaction_without_metadata() -> None:
    tx = TransactionUtils.createSignedP2PTransaction(
        PRIVATE_KEY,
        RECEIVER_ADDRESS,
        RECEIVER_AUTHKEY_PREFIX,
        # sequence
        255,
        # micro libra
        987_654_321,
        expiration_time=123_456_789,
        max_gas_amount=140000,
    )
    assert SIGNED_TXN_BYTES_WITHOUT_METADATA == bytes.hex(tx)


def test_sign_transaction_fail() -> None:
    with pytest.raises(ValueError):
        _ = TransactionUtils.createSignedP2PTransaction(
            bytes.fromhex("deadbeef"),
            RECEIVER_ADDRESS,
            RECEIVER_AUTHKEY_PREFIX,
            # sequence
            255,
            # micro libra
            987_654_321,
            expiration_time=123_456_789,
            max_gas_amount=140000,
        )


def test_parse_transaction_fail() -> None:
    with pytest.raises(ValueError):
        TransactionUtils.parse(0, bytes.fromhex("deadbeef"), GAS_USED)


def test_parse_transaction() -> None:
    tx = TransactionUtils.parse(0, bytes.fromhex(SIGNED_TXN_BYTES_HEX), GAS_USED)
    assert tx.version == 0
    assert tx.is_p2p
    assert tx.sender == ADDRESS
    assert tx.receiver == RECEIVER_ADDRESS
    assert tx.amount == 987_654_321
    assert tx.expiration_time == 123_456_789
    assert tx.gas_unit_price == 0
    assert tx.max_gas_amount == 140000
    assert tx.sequence == 255

    assert tx.public_key == PUBLIC_KEY
    assert tx.signature.hex() == SIGNATURE_BYTES.hex()
    assert tx.gas == GAS_USED
    assert tx.metadata == b"metadata"
