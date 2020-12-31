# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import typing, dataclasses, uuid

from .types import (
    CommandRequestObject,
    ErrorCode,
    PaymentObject,
    PaymentActorObject,
    KycDataObject,
    Status,
    FieldError,
    InvalidOverwriteError,
    new_payment_object,
    new_payment_request,
    replace_payment_actor,
    validate_write_once_fields,
)
from .error import command_error
from .payment_state import Action, Actor, MACHINE as payment_states, follow_up_action, summary, trigger_actor, R_SEND
from .state import ConditionValidationError, State
from .command import Command
from .. import diem_types, identifier, txnmetadata


@dataclasses.dataclass(frozen=True)
class PaymentCommand(Command):
    my_actor_address: str
    payment: PaymentObject
    inbound: bool
    cid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    @staticmethod
    def init(
        sender_account_id: str,
        sender_kyc_data: KycDataObject,
        receiver_account_id: str,
        amount: int,
        currency: str,
        original_payment_reference_id: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
        inbound: bool = False,
    ) -> "PaymentCommand":
        return PaymentCommand(
            my_actor_address=sender_account_id,
            payment=new_payment_object(
                sender_account_id,
                sender_kyc_data,
                receiver_account_id,
                amount,
                currency,
                original_payment_reference_id=original_payment_reference_id,
                description=description,
            ),
            inbound=inbound,
        )

    def id(self) -> str:
        return self.cid

    def is_inbound(self) -> bool:
        return self.inbound

    def reference_id(self) -> str:
        return self.payment.reference_id

    def follow_up_action(self) -> typing.Optional[Action]:
        return follow_up_action(self.my_actor(), self.state())

    def validate(self, prior: typing.Optional[Command]) -> None:
        prior = typing.cast(PaymentCommand, prior)
        try:
            self.validate_state_trigger_actor()
            if prior:
                self.validate_actor_object(prior)
                self.validate_write_once_fields(prior)
                self.validate_transition(prior)
            else:
                self.validate_is_initial()
        except FieldError as e:
            raise command_error(e.code, str(e), e.field) from e

    def validate_state_trigger_actor(self) -> None:
        if self.inbound and self.opponent_actor() != self.state_trigger_actor():
            raise command_error(
                ErrorCode.invalid_command_producer, f"{self.opponent_actor()} should not produce {self}"
            )

    def validate_actor_object(self, prior: "PaymentCommand") -> None:
        if self.inbound and self.my_actor_obj() != prior.my_actor_obj():
            raise InvalidOverwriteError(
                f"payment.{self.my_actor_field_name()}",
                self.my_actor_obj(),
                prior.my_actor_obj(),
                self.my_actor_field_name(),
            )

    def validate_is_initial(self) -> None:
        if not self.is_initial():
            msg = (
                f"{self} is not initial object, or could not find payment object by reference id: {self.reference_id()}"
            )
            raise command_error(ErrorCode.invalid_initial_or_prior_not_found, msg)

    def validate_transition(self, prior: "PaymentCommand") -> None:
        if not self.is_valid_transition(prior):
            raise command_error(ErrorCode.invalid_transition, f"can not transit from {prior} to {self}")

    def validate_write_once_fields(self, prior: "PaymentCommand") -> None:
        validate_write_once_fields("payment", self.payment, prior.payment)

    def new_command(
        self,
        recipient_signature: typing.Optional[str] = None,
        status: typing.Optional[str] = None,
        kyc_data: typing.Optional[KycDataObject] = None,
        additional_kyc_data: typing.Optional[str] = None,
        abort_code: typing.Optional[str] = None,
        abort_message: typing.Optional[str] = None,
        inbound: bool = False,
        metadata: typing.Optional[typing.List[str]] = None,
    ) -> Command:
        changes: typing.Dict[str, typing.Any] = {
            self.my_actor().value: replace_payment_actor(
                self.my_actor_obj(),
                status=status,
                kyc_data=kyc_data,
                additional_kyc_data=additional_kyc_data,
                abort_code=abort_code,
                abort_message=abort_message,
                metadata=metadata,
            ),
        }
        if recipient_signature:
            changes["recipient_signature"] = recipient_signature
        new_payment = dataclasses.replace(self.payment, **changes)
        return PaymentCommand(my_actor_address=self.my_actor_address, payment=new_payment, inbound=inbound)

    def new_request(self) -> CommandRequestObject:
        return new_payment_request(self.payment, self.cid)

    # the followings are PaymentCommand specific methods

    def is_sender(self) -> bool:
        return self.payment.sender.address == self.my_actor_address

    def is_receiver(self) -> bool:
        return self.payment.receiver.address == self.my_actor_address

    def my_actor_obj(self) -> PaymentActorObject:
        return self.payment.sender if self.is_sender() else self.payment.receiver

    def opponent_actor_obj(self) -> PaymentActorObject:
        return self.payment.receiver if self.is_sender() else self.payment.sender

    def my_actor(self) -> Actor:
        return Actor.SENDER if self.is_sender() else Actor.RECEIVER

    def opponent_actor(self) -> Actor:
        return Actor.RECEIVER if self.is_sender() else Actor.SENDER

    def my_actor_field_name(self) -> str:
        return self.my_actor().value

    def state(self) -> State[PaymentObject]:
        try:
            return payment_states.match_state(self.payment)
        except ConditionValidationError as e:
            fields = ", ".join(map(lambda f: f"command.payment.{f}", e.match_result.mismatched_fields))
            msg = f"payment object is invalid, missing: {fields}"
            raise command_error(ErrorCode.missing_field, msg, fields) from e

    def state_trigger_actor(self) -> Actor:
        return trigger_actor(self.state())

    def is_valid_transition(self, prior: "PaymentCommand") -> bool:
        return payment_states.is_valid_transition(prior.state(), self.state(), self.payment)

    def is_initial(self) -> bool:
        return payment_states.is_initial(self.state())

    def is_rsend(self) -> bool:
        return R_SEND == self.state()

    def is_both_ready(self) -> bool:
        return (
            self.payment.sender.status.status == Status.ready_for_settlement
            and self.payment.receiver.status.status == Status.ready_for_settlement
        )

    def is_abort(self) -> bool:
        return self.payment.sender.status.status == Status.abort or self.payment.receiver.status.status == Status.abort

    def receiver_account_address(self, hrp: str) -> diem_types.AccountAddress:
        return identifier.decode_account_address(self.payment.receiver.address, hrp)

    def receiver_subaddress(self, hrp: str) -> typing.Optional[bytes]:
        return identifier.decode_account_subaddress(self.payment.receiver.address, hrp)

    def sender_account_address(self, hrp: str) -> diem_types.AccountAddress:
        return identifier.decode_account_address(self.payment.sender.address, hrp)

    def sender_subaddress(self, hrp: str) -> typing.Optional[bytes]:
        return identifier.decode_account_subaddress(self.payment.sender.address, hrp)

    def travel_rule_metadata_signature_message(self, hrp: str) -> bytes:
        return self.travel_rule_metadata_and_sig_msg(hrp)[1]

    def travel_rule_metadata(self, hrp: str) -> bytes:
        return self.travel_rule_metadata_and_sig_msg(hrp)[0]

    def travel_rule_metadata_and_sig_msg(self, hrp: str) -> typing.Tuple[bytes, bytes]:
        return txnmetadata.travel_rule(
            self.payment.reference_id, self.sender_account_address(hrp), self.payment.action.amount
        )

    def __str__(self) -> str:
        return f"[payment#{self.cid} {self.my_actor_address} {summary(self.payment)}]"
