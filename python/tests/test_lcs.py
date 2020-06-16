# pyre-strict

from pylibra import TransactionUtils
from pylibra.libra_types import Transaction, ChangeSet, WriteSet, WriteSetMut
from pylibra import lcs


def test_lcs_e2e() -> None:
    print("Testing serialization: ")

    # pyre-ignore
    obj = Transaction.WaypointWriteSet(ChangeSet(WriteSet(WriteSetMut(write_set=[])), []))
    content = lcs.serialize(obj, Transaction)

    print("Serialization result: ", content)

    deobj, remaining = lcs.deserialize(content, Transaction)

    if remaining:
        raise ValueError("Remaining bytes: ", remaining)

    print("Deser result: ", deobj)

    assert obj == deobj


def test_lcs_e2e_native() -> None:
    content = TransactionUtils.createSignedP2PTransaction(
        bytes.fromhex("11" * 32), bytes.fromhex("22" * 16), 255, 1_234_567, expiration_time=123456789,
    )

    print("Testing Deserialization native bytes: ", content)

    # pyre-fixme
    deobj, remaining = lcs.deserialize(content, Transaction.UserTransaction)

    if remaining:
        raise ValueError("Remaining bytes: ", remaining)

    print("Deser result: ", deobj)

    print("Testing serialization again")

    new_content = lcs.serialize(deobj, Transaction.UserTransaction)

    print("Result:", new_content)

    assert new_content == content
