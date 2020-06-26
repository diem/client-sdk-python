# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
from pylibra import TransactionUtils, AccountKeyUtils

RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 16)
PRIVATE_KEY: bytes = bytes.fromhex("11" * 32)
PUBLIC_KEY: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).public_key
ADDRESS: bytes = AccountKeyUtils.from_private_key(PRIVATE_KEY).address

GAS_USED: int = 12


def test_parse_transaction_fail() -> None:
    with pytest.raises(ValueError):
        TransactionUtils.parse(0, bytes.fromhex("deadbeef"), GAS_USED)


def test_parse_transaction() -> None:
    tx_bytes = TransactionUtils.createSignedP2PTransaction(
        PRIVATE_KEY,
        RECEIVER_ADDRESS,
        # sequence
        255,
        # micro libra
        987_654_321,
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


def test_create_transcation() -> None:
    tx = TransactionUtils.createSignedRotateCompliancePublicKeyTransaction(
        PRIVATE_KEY, sender_private_key=PRIVATE_KEY, sender_sequence=255, expiration_time=123_456_789,
    )
    assert tx is not None

    tx = TransactionUtils.createSignedRotateBaseURLScriptTransaction(
        "test.test", sender_private_key=PRIVATE_KEY, sender_sequence=255, expiration_time=123_456_789,
    )
    assert tx is not None
