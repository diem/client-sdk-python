# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time
import typing

from dataclasses import dataclass, field as datafield

from .command_types import CommandType, UUID_REGEX


class KycDataObjectType:
    individual = "individual"
    entity = "entity"


class AbortCode:
    reject_kyc_data = "rejected"


class Status:
    # No status is yet set from this actor.
    none = "none"
    # KYC data about the subaddresses is required by this actor.
    needs_kyc_data = "needs_kyc_data"
    # Transaction is ready for settlement according to this actor
    ready_for_settlement = "ready_for_settlement"
    # Indicates the actor wishes to abort this payment, instead of settling it.
    abort = "abort"
    # KYC data resulted in a soft-match, request additional_kyc_data.
    soft_match = "soft_match"


@dataclass(frozen=True)
class StatusObject:
    # Status of the payment from the perspective of this actor. Required
    status: str = datafield(
        metadata={
            "valid-values": [
                Status.none,
                Status.needs_kyc_data,
                Status.ready_for_settlement,
                Status.abort,
                Status.soft_match,
            ]
        }
    )
    # In the case of an abort status, this field may be used to describe the reason for the abort.
    abort_code: typing.Optional[str] = datafield(default=None)
    # Additional details about this error. To be used only when code is populated
    abort_message: typing.Optional[str] = datafield(default=None)


@dataclass(frozen=True)
class NationalIdObject:
    # Indicates the national ID value - for example, a social security number
    id_value: str
    # Two-letter country code (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
    country: typing.Optional[str] = datafield(default=None)
    # Indicates the type of the ID
    type: typing.Optional[str] = datafield(default=None)


@dataclass(frozen=True)
class AddressObject:
    # The city, district, suburb, town, or village
    city: typing.Optional[str] = datafield(default=None)
    # Two-letter country code (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
    country: typing.Optional[str] = datafield(default=None)
    # Address line 1
    line1: typing.Optional[str] = datafield(default=None)
    # Address line 2 - apartment, unit, etc.
    line2: typing.Optional[str] = datafield(default=None)
    # ZIP or postal code
    postal_code: typing.Optional[str] = datafield(default=None)
    # State, county, province, region.
    state: typing.Optional[str] = datafield(default=None)


@dataclass(frozen=True)
class KycDataObject:
    # Must be either “individual” or “entity”. Required.
    type: str = datafield(metadata={"valid-values": [KycDataObjectType.individual, KycDataObjectType.entity]})
    # Version identifier to allow modifications to KYC data Object without needing to bump version of entire API set. Set to 1
    payload_version: int = datafield(default=1, metadata={"valid-values": [1]})
    # Legal given name of the user for which this KYC data Object applies.
    given_name: typing.Optional[str] = datafield(default=None)
    # Legal surname of the user for which this KYC data Object applies.
    surname: typing.Optional[str] = datafield(default=None)
    # Physical address data for this account
    address: typing.Optional[AddressObject] = datafield(default=None)
    # Date of birth for the holder of this account. Specified as an ISO 8601 calendar date format: https:#en.wikipedia.org/wiki/ISO_8601
    dob: typing.Optional[str] = datafield(default=None)
    # Place of birth for this user. line1 and line2 fields should not be populated for this usage of the address Object
    place_of_birth: typing.Optional[AddressObject] = datafield(default=None)
    # National ID information for the holder of this account
    national_id: typing.Optional[NationalIdObject] = datafield(default=None)
    # Name of the legal entity. Used when subaddress represents a legal entity rather than an individual. KycDataObject should only include one of legal_entity_name OR given_name/surname
    legal_entity_name: typing.Optional[str] = datafield(default=None)


@dataclass(frozen=True)
class PaymentActionObject:
    amount: int
    currency: str
    action: str = datafield(default="charge", metadata={"valid-values": ["charge"]})
    # Unix timestamp (seconds) indicating the time that the payment Command was created.
    timestamp: int = datafield(default_factory=lambda: int(time.time()))


@dataclass(frozen=True)
class PaymentActorObject:
    address: str = datafield(metadata={"write_once": True})
    status: StatusObject
    kyc_data: typing.Optional[KycDataObject] = datafield(default=None, metadata={"write_once": True})
    metadata: typing.Optional[typing.List[str]] = datafield(default=None)
    additional_kyc_data: typing.Optional[str] = datafield(default=None, metadata={"write_once": True})


@dataclass(frozen=True)
class PaymentObject:
    reference_id: str = datafield(metadata={"valid-values": UUID_REGEX})
    sender: PaymentActorObject
    receiver: PaymentActorObject
    action: PaymentActionObject = datafield(metadata={"write_once": True})
    original_payment_reference_id: typing.Optional[str] = datafield(
        default=None, metadata={"immutable": True, "valid-values": UUID_REGEX}
    )
    recipient_signature: typing.Optional[str] = datafield(default=None, metadata={"write_once": True})
    description: typing.Optional[str] = datafield(default=None, metadata={"write_once": True})


@dataclass(frozen=True)
class PaymentCommandObject:
    _ObjectType: str = datafield(metadata={"valid-values": [CommandType.PaymentCommand]})
    payment: PaymentObject
