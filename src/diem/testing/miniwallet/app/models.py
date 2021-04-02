# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field, asdict, fields
from enum import Enum
from typing import Optional, List, Dict, Any
from .... import identifier, offchain, diem_types
import json


@dataclass
class Base:
    id: str


@dataclass
class Account(Base):
    kyc_data: Optional[str] = field(default=None)
    reject_additional_kyc_data_request: Optional[bool] = field(default=False)

    def kyc_data_object(self) -> offchain.KycDataObject:
        if self.kyc_data:
            return offchain.from_json(str(self.kyc_data), offchain.KycDataObject)
        else:
            return offchain.individual_kyc_data()


@dataclass
class PaymentUri(Base):
    account_id: str
    payment_uri: str

    def intent(self, hrp: str) -> identifier.Intent:
        return identifier.decode_intent(self.payment_uri, hrp)


@dataclass
class Subaddress(Base):
    account_id: str
    subaddress_hex: str


@dataclass
class Payment(Base):
    account_id: str
    currency: str
    amount: int
    payee: str


@dataclass
class Event(Base):
    account_id: str
    type: str
    data: str
    timestamp: int


@dataclass
class KycSample:
    minimum: str
    reject: str
    soft_match: str
    soft_reject: str

    @staticmethod
    def gen(surname: str) -> "KycSample":
        def gen_kyc_data(name: str) -> str:
            return offchain.to_json(offchain.individual_kyc_data(given_name=name, surname=surname))

        return KycSample(**{f.name: gen_kyc_data("%s-kyc" % f.name) for f in fields(KycSample)})

    def match_kyc_data(self, field: str, kyc: offchain.KycDataObject) -> bool:
        subset = asdict(offchain.from_json(getattr(self, field), offchain.KycDataObject))
        return all(getattr(kyc, k) == v for k, v in subset.items() if v)

    def match_any_kyc_data(self, fields: List[str], kyc: offchain.KycDataObject) -> bool:
        return any(self.match_kyc_data(f, kyc) for f in fields)


class RefundReason(str, Enum):
    invalid_subaddress = "invalid_subaddress"
    other = "other"

    @staticmethod
    def from_diem_type(reason: diem_types.RefundReason) -> "RefundReason":
        if isinstance(reason, diem_types.RefundReason__InvalidSubaddress):
            return RefundReason.invalid_subaddress
        return RefundReason.other

    def to_diem_type(self) -> diem_types.RefundReason:
        return diem_types.RefundReason__InvalidSubaddress()


@dataclass
class Transaction(Base):
    class Status(str, Enum):
        completed = "completed"
        canceled = "canceled"
        pending = "pending"

    account_id: str
    currency: str
    amount: int
    status: Status
    cancel_reason: Optional[str] = field(default=None)
    payee: Optional[str] = field(default=None)
    subaddress_hex: Optional[str] = field(default=None)
    reference_id: Optional[str] = field(default=None)
    signed_transaction: Optional[str] = field(default=None)
    diem_transaction_version: Optional[int] = field(default=None)
    refund_diem_txn_version: Optional[int] = field(default=None)
    refund_reason: Optional[RefundReason] = field(default=None)

    def subaddress(self) -> bytes:
        return bytes.fromhex(str(self.subaddress_hex))

    def balance_amount(self) -> int:
        return -self.amount if self.payee else self.amount

    def __str__(self) -> str:
        return "Transaction %s" % json.dumps(asdict(self), indent=2)


@dataclass
class PaymentCommand(Base):
    account_id: str
    reference_id: str
    cid: str
    is_sender: bool
    payment_object: Dict[str, Any]
    is_inbound: bool = field(default=False)
    is_abort: bool = field(default=False)
    is_ready: bool = field(default=False)
    process_error: Optional[str] = field(default=None)

    def to_offchain_command(self) -> offchain.PaymentCommand:
        payment = offchain.from_dict(self.payment_object, offchain.PaymentObject)
        return offchain.PaymentCommand(
            my_actor_address=payment.sender.address if self.is_sender else payment.receiver.address,
            payment=payment,
            inbound=self.is_inbound,
            cid=self.cid,
        )
