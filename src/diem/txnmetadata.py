# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


"""LIP-4 Transaction Metadata Utilities

This module implements utility functions for application to create transaction metadata and metadata signature.
See https://dip.diem.com/dip-4 for more details
"""


from dataclasses import dataclass
import typing
import uuid
from . import diem_types, serde_types, bcs, jsonrpc, utils


class InvalidEventMetadataForRefundError(Exception):
    pass


@dataclass
class Attest:

    metadata: diem_types.Metadata
    sender_address: diem_types.AccountAddress
    amount: serde_types.uint64  # pyre-ignore

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, Attest)


def travel_rule(
    off_chain_reference_id: str, sender_address: diem_types.AccountAddress, amount: int
) -> typing.Tuple[bytes, bytes]:
    """Create travel rule metadata bytes and signature message bytes.

    This is used for peer to peer transfer between 2 custodial accounts.
    """

    metadata = diem_types.Metadata__TravelRuleMetadata(
        value=diem_types.TravelRuleMetadata__TravelRuleMetadataVersion0(
            value=diem_types.TravelRuleMetadataV0(off_chain_reference_id=off_chain_reference_id)
        )
    )

    # receiver_bcs_data = bcs(metadata, sender_address, amount) + "@@$$DIEM_ATTEST$$@@" /*ASCII-encoded string*/
    attest = Attest(metadata=metadata, sender_address=sender_address, amount=serde_types.uint64(amount))  # pyre-ignore
    signing_msg = attest.bcs_serialize() + b"@@$$DIEM_ATTEST$$@@"

    return (metadata.bcs_serialize(), signing_msg)


def decode_structure(
    bytes_or_str: typing.Union[bytes, str]
) -> typing.Union[
    None,
    diem_types.GeneralMetadataV0,
    diem_types.TravelRuleMetadataV0,
    diem_types.RefundMetadataV0,
    diem_types.PaymentMetadataV0,
]:
    """Decode given metadata bytes of string into structure types

    Returns None if:
    1. given param is empty or None
    2. metadata type is non-structured or undefined
    """

    if not bytes_or_str:
        return None
    b = bytes_or_str if isinstance(bytes_or_str, bytes) else bytes.fromhex(bytes_or_str)
    try:
        metadata = diem_types.Metadata.bcs_deserialize(b)
        return metadata.decode_structure()
    except serde_types.DeserializationError:
        return None


def refund_metadata(original_transaction_version: int, reason: diem_types.RefundReason) -> bytes:
    """Create refund metadata for peer to peer transaction script

    Use this function to create metadata when refunding a transaction, pass in the transaction version and
    a reason.

    List of reason types available:

    0. RefundReason__OtherReason
    1. RefundReason__InvalidSubaddress,
    2. RefundReason__UserInitiatedPartialRefund,
    3. RefundReason__UserInitiatedFullRefund,

    Example:

    ```
    >>> from diem import diem_types, txnmetadata
    >>> txnmetadata.refund_metadata(txn_version, diem_types.RefundReason__UserInitiatedFullRefund())

    """

    metadata = diem_types.Metadata__RefundMetadata(
        value=diem_types.RefundMetadata__RefundMetadataV0(
            value=diem_types.RefundMetadataV0(  # pyre-ignore
                transaction_version=original_transaction_version, reason=reason
            )
        )
    )
    return metadata.bcs_serialize()


def coin_trade_metadata(trade_ids: typing.List[str]) -> bytes:
    """Create `diem_types.Metadata__CoinTradeMetadata` with `diem_types.CoinTradeMetadataV0`"""

    metadata = diem_types.Metadata__CoinTradeMetadata(
        value=diem_types.CoinTradeMetadata__CoinTradeMetadataV0(
            value=diem_types.CoinTradeMetadataV0(trade_ids=trade_ids)
        )
    )
    return metadata.bcs_serialize()


def general_metadata(
    from_subaddress: typing.Optional[bytes] = None,
    to_subaddress: typing.Optional[bytes] = None,
    referenced_event: typing.Optional[int] = None,
) -> bytes:
    """Create general metadata for peer to peer transaction script

    Use this function to create metadata with from and to sub-addresses for peer to peer transfer
    from custodial account to custodial account under travel rule threshold.

    Give from_subaddress None for the case transferring from non-custodial to custodial account.
    Give to_subaddress None for the case transferring from custodial to non-custodial account.
    """

    metadata = diem_types.Metadata__GeneralMetadata(
        value=diem_types.GeneralMetadata__GeneralMetadataVersion0(
            value=diem_types.GeneralMetadataV0(  # pyre-ignore
                from_subaddress=from_subaddress,
                to_subaddress=to_subaddress,
                referenced_event=serde_types.uint64(referenced_event) if referenced_event else None,
            )
        )
    )
    return metadata.bcs_serialize()


def find_refund_reference_event(
    txn: typing.Optional[jsonrpc.Transaction], receiver: typing.Union[diem_types.AccountAddress, str]
) -> typing.Optional[jsonrpc.Event]:
    """Find refund reference event from given transaction

    The event can be used as reference is the "receivedpayment" event.
    We also only return event that receiver address matches given reciever address, because
    it is possible we may have mutliple receivers for one transaction in the future.

    Returns None if given transaction is None or the event not found.
    If this function returns an event, then you may call `refund_metadata_from_event` function
    to create refund metadata for the refund transaction.
    """

    if txn is None:
        return None

    address = utils.account_address_hex(receiver)
    for event in txn.events:
        if event.data.type == "receivedpayment" and event.data.receiver == address:
            return event

    return None


def payment_metadata(
    reference_id: str,
) -> bytes:
    """Create payment metadata for peer to peer transaction script

    Use this function to create metadata with a reference ID for peer to peer transfer
    under travel rule threshold.

    """

    metadata = diem_types.Metadata__PaymentMetadata(
        value=diem_types.PaymentMetadata__PaymentMetadataVersion0(
            value=diem_types.PaymentMetadataV0(  # pyre-ignore
                reference_id=uuid.UUID(reference_id).bytes,
            )
        )
    )
    return metadata.bcs_serialize()
