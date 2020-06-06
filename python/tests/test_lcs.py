# pyre-strict

from pylibra import TransactionUtils
from pylibra._lcs import lcs_bytes, lcs_from_bytes, Transaction, ChangeSet, WriteSet, WriteSetMut


def test_lcs_e2e() -> None:
    print("Testing serialization: ")

    # pyre-ignore
    obj = Transaction.WaypointWriteSet(ChangeSet(WriteSet(WriteSetMut(write_set=[])), []))
    content = lcs_bytes(obj, Transaction)

    print("Serialization result: ", content)

    deobj, remaining = lcs_from_bytes(content, Transaction)

    if remaining:
        raise ValueError("Remaining bytes: ", remaining)

    print("Deser result: ", deobj)

    assert obj == deobj


def test_lcs_e2e_native() -> None:
    p2p_script = TransactionUtils.createP2PTransactionScriptBytes(
        bytes.fromhex("22" * 16),
        bytes.fromhex("33" * 16),
        # micro libra
        987_654_321
    )

    content = TransactionUtils.createSignedTransaction(
        bytes.fromhex("11" * 32),
        255,
        script_bytes=p2p_script,
        expiration_time=123456789,
    )

    print("Testing Deserialization native bytes: ", content)

    # pyre-fixme
    deobj, remaining = lcs_from_bytes(content, Transaction.UserTransaction)

    if remaining:
        raise ValueError("Remaining bytes: ", remaining)

    print("Deser result: ", deobj)

    print("Testing serialization again")

    new_content = lcs_bytes(deobj, Transaction.UserTransaction)

    print("Result:", new_content)

    assert new_content == content
