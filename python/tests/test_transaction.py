# pyre-strict

import pytest
from pylibra import TransactionUtils, AccountKeyUtils

RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 16)
RECEIVER_AUTHKEY_PREFIX: bytes = bytes.fromhex("00" * 16)
PRIVATE_KEY: bytes = bytes.fromhex("11" * 32)
PUBLIC_KEY: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).public_key
ADDRESS: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).address

SIGNED_TXN_BYTES_HEX: str = (
    "6dfcea9ac61f0a8420e5d01fbd8f0ea8ff0000000000000002be01a11ceb0b0100070146"
    "00000004000000034a0000000c00000004560000000200000005580000000b0000000763"
    "00000037000000069a0000001000000009aa000000140000000000000101020001010100"
    "0300010101000204050a02030a0200010900063c53454c463e0c4c696272614163636f75"
    "6e741d7061795f66726f6d5f73656e6465725f776974685f6d65746164617461046d6169"
    "6e00000000000000000000000000000000010000ffff030006000a000b010a020b033e00"
    "02010600000000000000000000000000000000034c425201540004010000000000000000"
    "000000000000000002100000000000000000000000000000000000b168de3a0000000002"
    "086d65746164617461e0220200000000000000000000000000034c425215cd5b07000000"
    "000020d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c977873740"
    "097a4c291692ff76e01ff246edcb4244df1b2003719dd6c0d454884c6988e2fa58e749e3"
    "20435ed243f776b197538a13a2bfa2952639c883d6d68aaa176bd306"
)

SIGNED_TXN_BYTES_WITHOUT_METADATA: str = (
    "6dfcea9ac61f0a8420e5d01fbd8f0ea8ff0000000000000002be01a11ceb0b01000701460"
    "0000004000000034a0000000c00000004560000000200000005580000000b000000076300"
    "000037000000069a0000001000000009aa000000140000000000000101020001010100030"
    "0010101000204050a02030a0200010900063c53454c463e0c4c696272614163636f756e74"
    "1d7061795f66726f6d5f73656e6465725f776974685f6d65746164617461046d61696e000"
    "00000000000000000000000000000010000ffff030006000a000b010a020b033e00020106"
    "00000000000000000000000000000000034c4252015400040100000000000000000000000"
    "00000000002100000000000000000000000000000000000b168de3a000000000200e02202"
    "00000000000000000000000000034c425215cd5b07000000000020d04ab232742bb4ab3a1"
    "368bd4615e4e6d0224ab71a016baf8520a332c97787374069eeb5005244ead094fcd13510"
    "d1c025b7ba14037ee56e67c25c3ba4a25cd0cacc64c795ebc50c5fd2580ae8e7c463374b4"
    "66aa4bdf3c84b3bf820f4e5e37605"
)

SIGNATURE_BYTES: bytes = bytes.fromhex(
    "097a4c291692ff76e01ff246edcb4244df1b2003719dd6c0d454884c6988e2fa58e749e32"
    "0435ed243f776b197538a13a2bfa2952639c883d6d68aaa176bd306"
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
