# pyre-strict

import pytest
from pylibra import TransactionUtils, AccountKeyUtils

RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 16)
RECEIVER_AUTHKEY_PREFIX: bytes = bytes.fromhex("00" * 16)
PRIVATE_KEY: bytes = bytes.fromhex("11" * 32)
PUBLIC_KEY: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).public_key
ADDRESS: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).address

GAS_USED: int = 12


def test_parse_transaction_fail() -> None:
    with pytest.raises(ValueError):
        TransactionUtils.parse(0, bytes.fromhex("deadbeef"), GAS_USED)


def test_p2p_transaction() -> None:

    p2p_script = TransactionUtils.createP2PTransactionScriptBytes(
        RECEIVER_ADDRESS,
        RECEIVER_AUTHKEY_PREFIX,
        # micro libra
        987_654_321,
    )

    tx_bytes = TransactionUtils.createSignedTransaction(
        PRIVATE_KEY,
        # sequence
        255,
        script_bytes=p2p_script,
        expiration_time=123_456_789,
        max_gas_amount=140000,
    )

    tx = TransactionUtils.parse(0, tx_bytes, GAS_USED)
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
    assert tx.gas == GAS_USED
    assert tx.vm_status == 4000

def test_add_currency_transaction() -> None:
    pass
