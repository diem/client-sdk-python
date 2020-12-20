# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field as datafield

import re, time, typing


UUID_REGEX: typing.Pattern[str] = re.compile(
    "^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$", re.IGNORECASE
)


class KycDataObjectType:
    individual = "individual"
    entity = "entity"


class CommandType:
    PaymentCommand = "PaymentCommand"
    FundPullPreApprovalCommand = "FundPullPreApprovalCommand"


class CommandResponseStatus:
    success = "success"
    failure = "failure"


class OffChainErrorType:
    """command_error occurs in response to a Command failing to be applied - for example, invalid _reads values,
    or high level validation errors.
    protocol_error occurs in response to a failure related to the lower-level protocol.
    """

    command_error = "command_error"
    protocol_error = "protocol_error"


class AbortCode:
    reject_kyc_data = "rejected"


class ErrorCode:
    # PaymentActionObject#amount is under travel rule threshold, no kyc needed for the transaction
    no_kyc_needed = "no-kyc-needed"

    # can't transit from prior payment to new payment
    invalid_transition = "invalid-transition"

    # the producer of the command is not right actor, for example:
    # if next actor to change the payment is sender, but receiver send a new command with payment object change.
    # question: should we allow it for the case like appending metadata?
    invalid_command_producer = "invalid-command-producer"

    # object is not valid, type does not match
    invalid_object = "invalid-object"
    # missing required field, field value is required for a specific state
    # for example:
    #     1. when sender init the request, kyc_data is missing, or
    #     2. set sender#status#status to none at any time.
    missing_field = "missing-field"
    # field value type is wrong
    # field value is not one of expected values
    invalid_field_value = "invalid-field-value"
    unknown_field = "unknown-field"

    # request content is not valid json
    invalid_json = "invalid-json"

    # decode JWS content failed
    invalid_jws = "invalid-jws"
    # validate JWS signature failed
    invalid_jws_signature = "invalid-jws-signature"

    # request comment_type value is unknown
    unknown_command_type = "unknown-command-type"

    # 1. could not find actor's onchain account by address
    # 2. none of actor addresses is server's (parent / child) vasp or dd address
    unknown_actor_address = "unknown-actor-address"

    # overwrite write once / immutable field value
    invalid_overwrite = "invalid-overwrite"

    # could not find command by reference_id for a non-initial command
    invalid_initial_or_prior_not_found = "invalid-initial-or-prior-not-found"
    invalid_x_request_sender_address = "invalid-x-request-sender-address"

    # the command is conflict with another command updating in progress by reference id
    conflict = "conflict"

    missing_http_header = "missing-http-header"
    invalid_recipient_signature = "invalid-recipient-signature"


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
    original_payment_reference_id: typing.Optional[str] = datafield(default=None, metadata={"immutable": True})
    recipient_signature: typing.Optional[str] = datafield(default=None, metadata={"write_once": True})
    description: typing.Optional[str] = datafield(default=None, metadata={"write_once": True})


@dataclass(frozen=True)
class PaymentCommandObject:
    _ObjectType: str = datafield(metadata={"valid-values": [CommandType.PaymentCommand]})
    payment: PaymentObject


@dataclass(frozen=True)
class CommandRequestObject:
    # A unique identifier for the Command.
    cid: str = datafield(metadata={"valid-values": UUID_REGEX})
    # A string representing the type of Command contained in the request.
    command_type: str = datafield(
        metadata={"valid-values": [CommandType.PaymentCommand, CommandType.FundPullPreApprovalCommand]}
    )
    command: PaymentCommandObject
    _ObjectType: str = datafield(default="CommandRequestObject", metadata={"valid-values": ["CommandRequestObject"]})


@dataclass(frozen=True)
class OffChainErrorObject:
    # Either "command_error" or "protocol_error".
    type: str
    # The error code of the corresponding error
    code: str
    # The field on which this error occurred
    field: typing.Optional[str] = datafield(default=None)
    # Additional details about this error
    message: typing.Optional[str] = datafield(default=None)


@dataclass(frozen=True)
class CommandResponseObject:
    # Either success or failure.
    status: str = datafield(metadata={"valid-values": [CommandResponseStatus.success, CommandResponseStatus.failure]})
    # The fixed string CommandResponseObject.
    _ObjectType: str = datafield(default="CommandResponseObject", metadata={"valid-values": ["CommandResponseObject"]})
    # Details on errors when status == "failure"
    error: typing.Optional[OffChainErrorObject] = datafield(default=None)
    # The Command identifier to which this is a response.
    cid: typing.Optional[str] = datafield(default=None)
