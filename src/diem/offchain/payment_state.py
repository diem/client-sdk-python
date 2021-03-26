# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

""" This module defines states of `PaymentCommand` / `PaymentObject` for validating transitions
when an actor tries to update the `PaymentObject`.
"""

from .types import (
    StatusObject,
    Status,
    PaymentActorObject,
    PaymentObject,
    KycDataObject,
)
from .state import (
    Field,
    Machine,
    State,
    Value,
    build_machine,
    new_transition,
    require,
)
from .action import Action
from enum import Enum

import typing


class Actor(Enum):
    SENDER = "sender"
    RECEIVER = "receiver"


def status(actor: str, s: str) -> Value[PaymentObject, str]:
    return Value[PaymentObject, str](f"{actor}.status.status", s)


S_INIT: State[PaymentObject] = State(
    id="S_INIT",
    require=require(
        status("sender", Status.needs_kyc_data),
        status("receiver", Status.none),
        validation=Field(path="sender.kyc_data"),
    ),
)
S_ABORT: State[PaymentObject] = State(
    id="S_ABORT",
    require=require(
        status("sender", Status.abort),
    ),
)
S_SOFT: State[PaymentObject] = State(
    id="S_SOFT",
    require=require(
        status("sender", Status.soft_match),
        status("receiver", Status.ready_for_settlement),
        Field(path="receiver.additional_kyc_data", not_set=True),
    ),
)
S_SOFT_SEND: State[PaymentObject] = State(
    id="S_SOFT_SEND",
    require=require(
        status("sender", Status.needs_kyc_data),
        status("receiver", Status.soft_match),
        Field(path="sender.additional_kyc_data"),
    ),
)

READY: State[PaymentObject] = State(
    id="READY",
    require=require(
        status("sender", Status.ready_for_settlement),
        status("receiver", Status.ready_for_settlement),
    ),
)
R_ABORT: State[PaymentObject] = State(
    id="R_ABORT",
    require=require(
        status("receiver", Status.abort),
    ),
)
R_SOFT: State[PaymentObject] = State(
    id="R_SOFT",
    require=require(
        status("sender", Status.needs_kyc_data),
        status("receiver", Status.soft_match),
        Field(path="sender.additional_kyc_data", not_set=True),
    ),
)
R_SOFT_SEND: State[PaymentObject] = State(
    id="R_SOFT_SEND",
    require=require(
        status("sender", Status.soft_match),
        status("receiver", Status.ready_for_settlement),
        Field(path="receiver.additional_kyc_data"),
    ),
)
R_SEND: State[PaymentObject] = State(
    id="R_SEND",
    require=require(
        status("sender", Status.needs_kyc_data),
        status("receiver", Status.ready_for_settlement),
        validation=require(
            Field(path="receiver.kyc_data"),
            Field(path="recipient_signature"),
        ),
    ),
)


MACHINE: Machine[PaymentObject] = build_machine(
    [
        new_transition(S_INIT, R_SEND),
        new_transition(S_INIT, R_ABORT),
        new_transition(S_INIT, R_SOFT),
        new_transition(R_SEND, READY),
        new_transition(R_SEND, S_ABORT),
        new_transition(R_SEND, S_SOFT),
        new_transition(R_SOFT, S_SOFT_SEND),
        new_transition(R_SOFT, S_ABORT),
        new_transition(S_SOFT_SEND, R_ABORT),
        new_transition(S_SOFT_SEND, R_SEND),
        new_transition(S_SOFT, R_SOFT_SEND),
        new_transition(S_SOFT, R_ABORT),
        new_transition(R_SOFT_SEND, S_ABORT),
        new_transition(R_SOFT_SEND, READY),
    ]
)


FOLLOW_UP: typing.Dict[State[PaymentObject], typing.Optional[typing.Tuple[Actor, Action]]] = {
    S_INIT: (Actor.RECEIVER, Action.EVALUATE_KYC_DATA),
    R_SEND: (Actor.SENDER, Action.EVALUATE_KYC_DATA),
    R_ABORT: None,
    R_SOFT: (Actor.SENDER, Action.CLEAR_SOFT_MATCH),
    READY: (Actor.SENDER, Action.SUBMIT_TXN),
    S_ABORT: None,
    S_SOFT: (Actor.RECEIVER, Action.CLEAR_SOFT_MATCH),
    S_SOFT_SEND: (Actor.RECEIVER, Action.REVIEW_KYC_DATA),
    R_SOFT_SEND: (Actor.SENDER, Action.REVIEW_KYC_DATA),
}


def trigger_actor(state: State[PaymentObject]) -> Actor:
    """The actor triggers the action / event to produce the PaymentObject"""

    if state in [R_SEND, R_ABORT, R_SOFT, R_SOFT_SEND]:
        return Actor.RECEIVER
    return Actor.SENDER


def follow_up_action(actor: Actor, state: State[PaymentObject]) -> typing.Optional[Action]:
    """For the given actor and state, returns following up action"""

    followup = FOLLOW_UP[state]
    if not followup:
        return None
    follow_up_actor, action = followup
    return action if follow_up_actor == actor else None


def summary(
    obj: typing.Union[
        PaymentObject,
        PaymentActorObject,
        StatusObject,
        KycDataObject,
        str,
        None,
    ]
) -> str:
    """summary returns a short summary string for a `PaymentObject`.

    flags:

    - `-`: value is not exist or not set
    - `s`: status is set
    - `k`: KYC data object is set
    - `+`: additional KYC data is set
    - `_`: flags connector
    - `?`: unknown data
    """

    if obj is None:
        return "-"
    if isinstance(obj, str):
        return "s"
    if isinstance(obj, KycDataObject):
        return "k"
    if isinstance(obj, StatusObject):
        return obj.status
    if isinstance(obj, PaymentActorObject):
        kyc = summary(obj.kyc_data)
        if obj.additional_kyc_data:
            kyc += "+"
        return "_".join([summary(obj.status), kyc])
    if isinstance(obj, PaymentObject):
        return "_".join(
            [
                summary(obj.sender),
                summary(obj.receiver),
                summary(obj.recipient_signature),
            ]
        )
    return "?"
