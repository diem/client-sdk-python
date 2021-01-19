# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing
import uuid

from . import FundPullPreApprovalObject, CommandType, CommandRequestObject
from .command import Command
from .payment_state import Action
from .types import new_funds_pull_pre_approval_request


@dataclasses.dataclass(frozen=True)
class FundsPullPreApprovalCommand(Command):
    my_actor_address: str
    funds_pull_pre_approval: FundPullPreApprovalObject
    cid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    def command_type(self) -> str:
        return CommandType.FundPullPreApprovalCommand

    def id(self) -> str:
        return self.cid

    def follow_up_action(self) -> typing.Optional[Action]:
        pass

    def reference_id(self) -> str:
        return self.funds_pull_pre_approval.funds_pull_pre_approval_id

    def validate(self, prior: typing.Optional["Command"]) -> None:
        pass

    def my_address(self) -> str:
        return self.my_actor_address

    def opponent_address(self) -> str:
        if self.my_actor_address == self.funds_pull_pre_approval.biller_address:
            return self.funds_pull_pre_approval.address
        else:
            return self.funds_pull_pre_approval.biller_address

    def new_request(self) -> CommandRequestObject:
        return new_funds_pull_pre_approval_request(funds_pull_pre_approval=self.funds_pull_pre_approval, cid=self.cid)
