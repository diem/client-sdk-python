# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

# pyre-strict

from pylibra import TransactionUtils
from pylibra import libra_types as libra
from pylibra import serde_types as st
from pylibra import lcs
from pylibra import stdlib


def test_lcs_e2e() -> None:
    print("Testing serialization: ")

    obj = libra.Transaction__GenesisTransaction(
        libra.WriteSetPayload__Direct(libra.ChangeSet(libra.WriteSet(libra.WriteSetMut(write_set=[])), []))
    )
    content = lcs.serialize(obj, libra.Transaction)

    print("Serialization result: ", content)

    deobj, remaining = lcs.deserialize(content, libra.Transaction)

    if remaining:
        raise ValueError("Remaining bytes: ", remaining)

    print("Deser result: ", deobj)

    assert obj == deobj


def test_lcs_e2e_native() -> None:
    content = TransactionUtils.createSignedP2PTransaction(
        bytes.fromhex("11" * 32), bytes.fromhex("22" * 16), 255, 1_234_567, expiration_time=123456789, chain_id=255
    )

    print("Testing Deserialization native bytes: ", content)

    deobj, remaining = lcs.deserialize(content, libra.Transaction__UserTransaction)

    if remaining:
        raise ValueError("Remaining bytes: ", remaining)

    print("Deser result: ", deobj)

    print("Testing serialization again")

    new_content = lcs.serialize(deobj, libra.Transaction__UserTransaction)

    print("Result:", new_content)

    assert new_content == content


def make_address(content: bytes) -> libra.AccountAddress:
    assert len(content) == 16
    # pyre-fixme
    return libra.AccountAddress(tuple(st.uint8(x) for x in content))


def test_stdlib() -> None:
    content = TransactionUtils.createSignedP2PTransaction(
        bytes.fromhex("11" * 32), bytes.fromhex("22" * 16), 255, 1_234_567, expiration_time=123456789, chain_id=255
    )
    raw_txn = lcs.deserialize(content, libra.Transaction__UserTransaction)[0].value.raw_txn

    assert isinstance(raw_txn.payload, libra.TransactionPayload__Script)

    token = libra.TypeTag__Struct(
        libra.StructTag(
            address=make_address(b"\x00" * 15 + b"\x01"),
            module=libra.Identifier("LBR"),
            name=libra.Identifier("LBR"),
            type_params=[],
        )
    )
    payee = make_address(b"\x22" * 16)
    amount = st.uint64(1_234_567)
    script = stdlib.encode_peer_to_peer_with_metadata_script(token, payee, amount, b"", b"")

    # We have successfully generated an (unsigned) P2P transaction in python.
    assert script == raw_txn.payload.value
