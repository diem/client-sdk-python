# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import re
import typing
from dataclasses import dataclass, field as datafield


UUID_REGEX: typing.Pattern[str] = re.compile(
    "^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$", re.IGNORECASE
)


class CommandType:
    PaymentCommand = "PaymentCommand"
    FundPullPreApprovalCommand = "FundPullPreApprovalCommand"


class CommandResponseStatus:
    success = "success"
    failure = "failure"


class ErrorCode:
    # PaymentActionObject#amount is under travel rule threshold, no kyc needed for
    # the transaction
    no_kyc_needed = "no-kyc-needed"

    # can't transit from prior payment to new payment
    invalid_transition = "invalid-transition"

    # the producer of the command is not right actor, for example:
    # if next actor to change the payment is sender, but receiver send a new command
    # with payment object change.
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


class OffChainErrorType:
    """command_error occurs in response to a Command failing to be applied -
    for example, invalid _reads values, or high level validation errors.
    protocol_error occurs in response to a failure related to the lower-level protocol.
    """

    command_error = "command_error"
    protocol_error = "protocol_error"


# Late import to solve circular dependency and be able to list all the command types
from .payment_types import PaymentCommandObject


@dataclass(frozen=True)
class FundPullPreApprovalCommandObject:
    _ObjectType: str = datafield(metadata={"valid-values": [CommandType.FundPullPreApprovalCommand]})


@dataclass(frozen=True)
class CommandRequestObject:
    # A unique identifier for the Command.
    cid: str = datafield(metadata={"valid-values": UUID_REGEX})
    # A string representing the type of Command contained in the request.
    command_type: str = datafield(
        metadata={"valid-values": [CommandType.PaymentCommand, CommandType.FundPullPreApprovalCommand]}
    )
    command: typing.Union[PaymentCommandObject, FundPullPreApprovalCommandObject]
    _ObjectType: str = datafield(default="CommandRequestObject", metadata={"valid-values": ["CommandRequestObject"]})


@dataclass(frozen=True)
class OffChainErrorObject:
    # Either "command_error" or "protocol_error".
    type: str = datafield(
        metadata={
            "valid-values": [
                OffChainErrorType.command_error,
                OffChainErrorType.protocol_error,
            ]
        }
    )
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
