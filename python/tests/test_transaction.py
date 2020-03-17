# pyre-strict
import pytest
from pylibra import TransactionUtils, AccountKey

RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 32)
PRIVATE_KEY: bytes = bytes.fromhex("11" * 32)
PUBLIC_KEY: bytes = AccountKey(PRIVATE_KEY).public_key
ADDRESS: bytes = AccountKey(PRIVATE_KEY).address

SIGNED_TXN_BYTES_HEX: str = (
    "a07ffc5e1799c00f3ac9fa7bbf1db75a25aaf4d0ac1e104f3f16a5445cd9c571ff0000000000000002000000b4000000"
    "a11ceb0b010007014600000004000000034a000000060000000c50000000060000000d5600000006000000055c000000"
    "2900000004850000002000000007a50000000f00000000000002000100010300020002050300030205030300063c5345"
    "4c463e046d61696e0c4c696272614163636f756e740f7061795f66726f6d5f73656e6465720000000000000000000000"
    "000000000000000000000000000000000000000000000000020004000b000b0112010102020000000100000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000b168de3a00000000e022020000000000"
    "000000000000000015cd5b070000000020000000d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332"
    "c977873740000000c5c827997b79e2f9d5d85d0729dcd2957ebb62eab45590ea98a19db9c7325044195d2a86f6e4b53d"
    "d20c0c6df80dbecfe8d800828fe8c64cd354cfab801c7708"
)

SIGNATURE_BYTES: bytes = bytes.fromhex(
    "c5c827997b79e2f9d5d85d0729dcd2957ebb62eab45590ea98a19db9c7325044195d2a86f6e4b53dd20c0c6df80dbecf"
    "e8d800828fe8c64cd354cfab801c7708"
)

GAS_USED: int = 12


def test_sign_transaction() -> None:
    tx = TransactionUtils.createSignedP2PTransaction(
        PRIVATE_KEY,
        RECEIVER_ADDRESS,
        b"",
        # sequence
        255,
        # micro libra
        987_654_321,
        expiration_time=123_456_789,
    )

    assert SIGNED_TXN_BYTES_HEX == tx.hex


def test_sign_transaction_fail() -> None:
    with pytest.raises(ValueError):
        _ = TransactionUtils.createSignedP2PTransaction(
            bytes.fromhex("deadbeef"),
            RECEIVER_ADDRESS,
            b"",
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
