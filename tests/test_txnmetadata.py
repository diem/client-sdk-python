# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

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
    assert ret.hex() == "0100000000"


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


def test_refund_metadata():
    txn_version = 12343
    reason = diem_types.RefundReason__UserInitiatedFullRefund()
    ret = txnmetadata.refund_metadata(txn_version, reason)
    assert ret.hex() == "0400373000000000000003"


def test_coin_trade_metadata():
    trade_ids = ["abc", "efg"]
    ret = txnmetadata.coin_trade_metadata(trade_ids)
    assert ret.hex() == "0500020361626303656667"
    metadata = txnmetadata.decode_structure(ret)
    assert metadata.trade_ids == trade_ids


def test_payment_metadata():
    reference_id = "ba199cc9-eca4-4475-bb7a-9e3b53de8547"
    ret = txnmetadata.payment_metadata(reference_id)
    assert ret.hex() == "0600ba199cc9eca44475bb7a9e3b53de8547"


def test_decode_structure():
    assert txnmetadata.decode_structure(None) is None
    assert txnmetadata.decode_structure("") is None
    assert txnmetadata.decode_structure(b"") is None
    assert txnmetadata.decode_structure(b"hello world") is None

    gm = txnmetadata.decode_structure("010001088f8b82153010a1bd0000")
    assert isinstance(gm, diem_types.GeneralMetadataV0)
    tr = txnmetadata.decode_structure("020001166f666620636861696e207265666572656e6365206964")
    assert isinstance(tr, diem_types.TravelRuleMetadataV0)
    refund = txnmetadata.decode_structure("0400373000000000000003")
    assert isinstance(refund, diem_types.RefundMetadataV0)
    trade = txnmetadata.decode_structure("050000")
    assert isinstance(trade, diem_types.CoinTradeMetadataV0)
    payment = txnmetadata.decode_structure("0600ffb6a935ab074dc2a47ee5c178d9d0ca")
    assert isinstance(payment, diem_types.PaymentMetadataV0)

    # UnstructuredBytesMetadata
    assert txnmetadata.decode_structure("03010461626364") is None
