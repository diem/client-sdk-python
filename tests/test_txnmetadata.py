# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
from diem import utils, txnmetadata, jsonrpc, diem_types


def test_travel_rule_metadata():
    address = utils.account_address("f72589b71ff4f8d139674a3f7369c69b")
    metadata, sig_msg = txnmetadata.travel_rule("off chain reference id", address, 1000)

    assert metadata.hex() == "020001166f666620636861696e207265666572656e6365206964"
    assert (
        sig_msg.hex()
        == "020001166f666620636861696e207265666572656e6365206964f72589b71ff4f8d139674a3f7369c69be803000000000000404024244449454d5f41545445535424244040"
    )


def test_new_general_metadata_for_nones():
    ret = txnmetadata.general_metadata(None, None)
    assert ret == b""


def test_new_general_metadata_to_sub_address():
    sub_address = utils.sub_address("8f8b82153010a1bd")
    ret = txnmetadata.general_metadata(None, sub_address)
    assert ret.hex() == "010001088f8b82153010a1bd0000"


def test_new_general_metadata_from_sub_address():
    sub_address = utils.sub_address("8f8b82153010a1bd")
    ret = txnmetadata.general_metadata(sub_address)
    assert ret.hex() == "01000001088f8b82153010a1bd00"


def test_new_general_metadata_from_to_sub_address():
    from_sub_address = utils.sub_address("8f8b82153010a1bd")
    to_sub_address = utils.sub_address("111111153010a111")

    ret = txnmetadata.general_metadata(from_sub_address, to_sub_address)
    assert ret.hex() == "01000108111111153010a11101088f8b82153010a1bd00"


def test_find_refund_reference_event():
    # None for no transaction given
    assert txnmetadata.find_refund_reference_event(None, None) is None

    receiver = utils.account_address("f72589b71ff4f8d139674a3f7369c69b")
    txn = jsonrpc.Transaction()
    txn.events.add(data=jsonrpc.EventData(type="unknown", receiver="f72589b71ff4f8d139674a3f7369c69b"))
    txn.events.add(data=jsonrpc.EventData(type="receivedpayment", receiver="unknown"))

    # None for not found
    event = txnmetadata.find_refund_reference_event(txn, receiver)
    assert event is None

    txn.events.add(data=jsonrpc.EventData(type="receivedpayment", receiver="f72589b71ff4f8d139674a3f7369c69b"))
    event = txnmetadata.find_refund_reference_event(txn, receiver)
    assert event is not None
    assert event.data.type == "receivedpayment"
    assert event.data.receiver == "f72589b71ff4f8d139674a3f7369c69b"


def test_refund_metadata_from_event():
    from_sub_address = "8f8b82153010a1bd"
    to_sub_address = "111111153010a111"
    reference_event_seq = 324

    metadata = txnmetadata.general_metadata(utils.sub_address(from_sub_address), utils.sub_address(to_sub_address))
    event = jsonrpc.Event(
        data=jsonrpc.EventData(
            metadata=metadata.hex(),
        ),
        sequence_number=reference_event_seq,
    )

    ret = txnmetadata.refund_metadata_from_event(event)
    assert ret is not None

    gm = diem_types.Metadata__GeneralMetadata.bcs_deserialize(ret)
    assert gm is not None
    assert gm.value.value.from_subaddress.hex() == to_sub_address
    assert gm.value.value.to_subaddress.hex() == from_sub_address
    assert int(gm.value.value.referenced_event) == reference_event_seq


def test_refund_metadata_from_event_that_has_from_subaddress():
    from_sub_address = "8f8b82153010a1bd"
    reference_event_seq = 324

    metadata = txnmetadata.general_metadata(utils.sub_address(from_sub_address))
    event = jsonrpc.Event(
        data=jsonrpc.EventData(
            metadata=metadata.hex(),
        ),
        sequence_number=reference_event_seq,
    )

    ret = txnmetadata.refund_metadata_from_event(event)
    assert ret is not None

    gm = diem_types.Metadata__GeneralMetadata.bcs_deserialize(ret)
    assert gm is not None
    assert gm.value.value.from_subaddress is None
    assert gm.value.value.to_subaddress.hex() == from_sub_address
    assert int(gm.value.value.referenced_event) == reference_event_seq


def test_refund_metadata_from_event_that_has_to_subaddress():
    to_sub_address = "8f8b82153010a1bd"
    reference_event_seq = 324

    metadata = txnmetadata.general_metadata(None, utils.sub_address(to_sub_address))
    event = jsonrpc.Event(
        data=jsonrpc.EventData(
            metadata=metadata.hex(),
        ),
        sequence_number=reference_event_seq,
    )

    ret = txnmetadata.refund_metadata_from_event(event)
    assert ret is not None

    gm = diem_types.Metadata__GeneralMetadata.bcs_deserialize(ret)
    assert gm is not None
    assert gm.value.value.from_subaddress.hex() == to_sub_address
    assert gm.value.value.to_subaddress is None
    assert int(gm.value.value.referenced_event) == reference_event_seq


def test_event_metadata_is_not_hex_encoded_string():
    event = jsonrpc.Event(
        data=jsonrpc.EventData(
            metadata="random",
        ),
        sequence_number=32,
    )
    with pytest.raises(txnmetadata.InvalidEventMetadataForRefundError):
        txnmetadata.refund_metadata_from_event(event)


def test_event_metadata_is_not_bcs_string():
    event = jsonrpc.Event(
        data=jsonrpc.EventData(
            metadata="1111122222",
        ),
        sequence_number=32,
    )
    with pytest.raises(txnmetadata.InvalidEventMetadataForRefundError):
        txnmetadata.refund_metadata_from_event(event)


def test_event_metadata_is_none_or_empty():
    event = jsonrpc.Event(
        data=jsonrpc.EventData(
            metadata=None,
        ),
        sequence_number=32,
    )
    assert txnmetadata.refund_metadata_from_event(event) == b""

    event = jsonrpc.Event(
        data=jsonrpc.EventData(
            metadata="",
        ),
        sequence_number=32,
    )
    assert txnmetadata.refund_metadata_from_event(event) == b""
