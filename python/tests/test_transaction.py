# pyre-strict

import pytest
from pylibra import TransactionUtils, AccountKeyUtils

RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 16)
RECEIVER_AUTHKEY_PREFIX: bytes = bytes.fromhex("00" * 16)
PRIVATE_KEY: bytes = bytes.fromhex("11" * 32)
PUBLIC_KEY: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).public_key
ADDRESS: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).address

SIGNED_TXN_BYTES_HEX: str = (
    "6dfcea9ac61f0a8420e5d01fbd8f0ea8ff0000000000000002cd01a11ceb0b010008014f"
    "000000060000000255000000040000000359000000060000000c5f000000110000000d70"
    "0000000b000000057b0000002f00000004aa0000001000000007ba000000130000000000"
    "0001000201030200020400000501020003050a02030101020003050a0203000303050a02"
    "030301080000063c53454c463e034c42520c4c696272614163636f756e7401540f706179"
    "5f66726f6d5f73656e646572046d61696e00000000000000000000000000000000010000"
    "ffff030005000a000b010a02120001020301000000000000000000000000000000000210"
    "0000000000000000000000000000000000b168de3a00000000e022020000000000000000"
    "00000000000600000000000000000000000000000000034c425201540015cd5b07000000"
    "000020d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c977873740"
    "7f8765bc07fd226e3ef8ec7390c9c9ad5331a99a0122dd56bbcea0ab3e5e3fc6ef37ac80"
    "5ed9e2c4f369f9664983d2388faaef6d7e0201174d357df3a34fae00"
)

SIGNATURE_BYTES: bytes = bytes.fromhex(
    "7f8765bc07fd226e3ef8ec7390c9c9ad5331a99a0122dd56bbcea0ab3e5e3fc6ef37ac80"
    "5ed9e2c4f369f9664983d2388faaef6d7e0201174d357df3a34fae00"
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
    )

    assert SIGNED_TXN_BYTES_HEX == bytes.hex(tx)


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
