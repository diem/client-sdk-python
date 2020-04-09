# pyre-strict

import pytest
from pylibra import TransactionUtils, AccountKeyUtils

RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 16)
RECEIVER_AUTHKEY_PREFIX: bytes = bytes.fromhex("00" * 16)
PRIVATE_KEY: bytes = bytes.fromhex("11" * 32)
PUBLIC_KEY: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).public_key
ADDRESS: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).address

SIGNED_TXN_BYTES_HEX: str = (
    "6dfcea9ac61f0a8420e5d01fbd8f0ea8ff0000000000000002ac01a11ceb0b010007014"
    "600000004000000034a0000000c00000004560000000200000005580000000900000007"
    "6100000029000000068a00000010000000099a000000120000000000000101020001010"
    "1000300010101000203050a020300010900063c53454c463e0c4c696272614163636f75"
    "6e740f7061795f66726f6d5f73656e646572046d61696e0000000000000000000000000"
    "0000000010000ffff030005000a000b010a023e00020106000000000000000000000000"
    "00000000034c42520154000301000000000000000000000000000000000210000000000"
    "0000000000000000000000000b168de3a00000000e02202000000000000000000000000"
    "000600000000000000000000000000000000034c425201540015cd5b07000000000020d"
    "04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737407ceff5"
    "d4e5c41d004aab4d9081a49fd338bb651eac58b5f543ac79d064e4277f2fbfc9cd51052"
    "e58926e5d1e9cd425f982e88f9a85834428a9c5d1928e3bd009"
)

SIGNATURE_BYTES: bytes = bytes.fromhex(
    "7ceff5d4e5c41d004aab4d9081a49fd338bb651eac58b5f543ac79d064e4277f2fbfc9c"
    "d51052e58926e5d1e9cd425f982e88f9a85834428a9c5d1928e3bd009"
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
