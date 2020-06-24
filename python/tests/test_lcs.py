from pylibra import TransactionUtils
from pylibra import libra_types as libra
from pylibra import serde_types as st
from pylibra import lcs
from pylibra import stdlib


def test_lcs_e2e() -> None:
    print("Testing serialization: ")

    # pyre-ignore
    obj = libra.Transaction.WaypointWriteSet(libra.ChangeSet(libra.WriteSet(libra.WriteSetMut(write_set=[])), []))
    content = lcs.serialize(obj, libra.Transaction)

    print("Serialization result: ", content)

    deobj, remaining = lcs.deserialize(content, libra.Transaction)

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
    deobj, remaining = lcs.deserialize(content, libra.Transaction.UserTransaction)

    if remaining:
        raise ValueError("Remaining bytes: ", remaining)

    print("Deser result: ", deobj)

    print("Testing serialization again")

    new_content = lcs.serialize(deobj, libra.Transaction.UserTransaction)

    print("Result:", new_content)

    assert new_content == content


def test_stdlib() -> None:
    content = TransactionUtils.createSignedP2PTransaction(
        bytes.fromhex("11" * 32), bytes.fromhex("22" * 16), 255, 1_234_567, expiration_time=123456789,
    )
    # pyre-fixme
    raw_txn = lcs.deserialize(content, libra.Transaction.UserTransaction)[0].value.raw_txn

    # pyre-fixme
    assert isinstance(raw_txn.payload, libra.TransactionPayload.Script)

    # pyre-fixme
    token = libra.TypeTag.Struct(
        value=libra.StructTag(
            address=libra.AccountAddress(value=(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)),
            module=libra.Identifier(value="LBR"),
            name=libra.Identifier(value="LBR"),
            type_params=[],
        )
    )
    # pyre-fixme
    payee = libra.AccountAddress((0x22,) * 16)
    amount = st.uint64(1_234_567)
    script = stdlib.encode_peer_to_peer_with_metadata_script(token, payee, amount, [], [])

    # We have successfully generated an (unsigned) P2P transaction in python.
    assert script == raw_txn.payload.value
