# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing
import uuid

from . import FundPullPreApprovalObject, CommandType, CommandRequestObject
from . import funds_pull_pre_approval_command_state as state_machine
from .command import Command
from .error import command_error
from .payment_state import Action
from .types import new_funds_pull_pre_approval_request, ErrorCode, FieldError, validate_write_once_fields


@dataclasses.dataclass(frozen=True)
class FundsPullPreApprovalCommand(Command):
    my_actor_address: str
    funds_pull_pre_approval: FundPullPreApprovalObject
    inbound: bool
    cid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    def id(self) -> str:
        return self.cid

    def command_type(self) -> str:
        return CommandType.FundPullPreApprovalCommand

    def is_inbound(self) -> bool:
        return self.inbound

    def follow_up_action(self) -> typing.Optional[Action]:
        pass

    def reference_id(self) -> str:
        return self.funds_pull_pre_approval.funds_pull_pre_approval_id

    def validate(self, prior: typing.Optional["Command"]) -> None:
        prior = typing.cast(FundsPullPreApprovalCommand, prior)
        try:
            if prior:
                self.validate_transition(prior)
                self.validate_write_once_fields(prior)
            else:
                self.validate_is_initial()
        except FieldError as e:
            raise command_error(e.code, str(e), e.field) from e

    def validate_is_initial(self) -> None:
        if not state_machine.is_valid_initial_status(self.funds_pull_pre_approval.status):
            msg = f"{self} is not in a valid initial state"
            raise command_error(ErrorCode.invalid_initial_or_prior_not_found, msg)

    def validate_transition(self, prior: "FundsPullPreApprovalCommand") -> None:
        current_status = prior.funds_pull_pre_approval.status
        next_status = self.funds_pull_pre_approval.status
        if not state_machine.is_valid_transition(current_status, next_status):
            raise command_error(ErrorCode.invalid_transition, f"can not transit from {prior} to {self}")

    def validate_write_once_fields(self, prior: "FundsPullPreApprovalCommand") -> None:
        validate_write_once_fields(
            "funds_pull_pre_approval", self.funds_pull_pre_approval, prior.funds_pull_pre_approval
        )

    def my_address(self) -> str:
        return self.my_actor_address

    def opponent_address(self) -> str:
        if self.my_actor_address == self.funds_pull_pre_approval.biller_address:
            return self.funds_pull_pre_approval.address
        else:
            return self.funds_pull_pre_approval.biller_address

    def new_request(self) -> CommandRequestObject:
        return new_funds_pull_pre_approval_request(funds_pull_pre_approval=self.funds_pull_pre_approval, cid=self.cid)
