# pyre-strict

import pytest
from pylibra import TransactionUtils, AccountKeyUtils

RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 16)
RECEIVER_AUTHKEY_PREFIX: bytes = bytes.fromhex("00" * 16)
PRIVATE_KEY: bytes = bytes.fromhex("11" * 32)
PUBLIC_KEY: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).public_key
ADDRESS: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).address

SIGNED_TXN_BYTES_HEX: str = (
    "6dfcea9ac61f0a8420e5d01fbd8f0ea8ff00000000000000028302a11ceb0b0100070146"
    "00000004000000034a00000017000000046100000004000000056500000018000000077d"
    "0000005600000008d30000001000000009e3000000200000000000000101020001010101"
    "030203000104040101010005050101010006020602050a0200010501010305030a020405"
    "0a02030a02010900063c53454c463e0c4c696272614163636f756e74176372656174655f"
    "756e686f737465645f6163636f756e74066578697374731d7061795f66726f6d5f73656e"
    "6465725f776974685f6d65746164617461046d61696e0000000000000000000000000000"
    "0000030000050d000a001101200305000508000a000a013d000a000a020b033d01020106"
    "00000000000000000000000000000000034c425201540004010000000000000000000000"
    "000000000002100000000000000000000000000000000000b168de3a0000000002086d65"
    "746164617461e022020000000000000000000000000015cd5b07000000000020d04ab232"
    "742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c977873740203e6faf9d896b"
    "6a859614ff926e2001e5a753082d5e85a4aa0192f67f3b9139587b0757b928851db28d54"
    "7db7cd6e6724871d2dc6bf121d5727c6c92f5a170c"
)

SIGNED_TXN_BYTES_WITHOUT_METADATA: str = (
    "6dfcea9ac61f0a8420e5d01fbd8f0ea8ff00000000000000028302a11ceb0b0100070146"
    "00000004000000034a00000017000000046100000004000000056500000018000000077d"
    "0000005600000008d30000001000000009e3000000200000000000000101020001010101"
    "030203000104040101010005050101010006020602050a0200010501010305030a020405"
    "0a02030a02010900063c53454c463e0c4c696272614163636f756e74176372656174655f"
    "756e686f737465645f6163636f756e74066578697374731d7061795f66726f6d5f73656e"
    "6465725f776974685f6d65746164617461046d61696e0000000000000000000000000000"
    "0000030000050d000a001101200305000508000a000a013d000a000a020b033d01020106"
    "00000000000000000000000000000000034c425201540004010000000000000000000000"
    "000000000002100000000000000000000000000000000000b168de3a000000000200e022"
    "020000000000000000000000000015cd5b07000000000020d04ab232742bb4ab3a1368bd"
    "4615e4e6d0224ab71a016baf8520a332c977873740f215dae13e0e0408964491221c9152"
    "7f1387a5f058cb13e73acbfa8f3a3d2b434ce0360f5cc617a83a0b2d5782fff8a7fa7a4c"
    "d56b6ee61533962bdd2b06490f"
)

SIGNATURE_BYTES: bytes = bytes.fromhex(
    "203e6faf9d896b6a859614ff926e2001e5a753082d5e85a4aa0192f67f3b9139587b0757"
    "b928851db28d547db7cd6e6724871d2dc6bf121d5727c6c92f5a170c"
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
