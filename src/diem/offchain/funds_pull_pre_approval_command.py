# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing
import uuid

from . import FundPullPreApprovalObject, CommandType
from .command import Command
from .payment_state import Action


@dataclasses.dataclass(frozen=True)
class FundsPullPreApprovalCommand(Command):
    funds_pull_pre_approval: FundPullPreApprovalObject
    cid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    def command_type(self) -> str:
        return CommandType.FundPullPreApprovalCommand

    def id(self) -> str:
        return self.cid

    def is_inbound(self) -> bool:
        pass

    def follow_up_action(self) -> typing.Optional[Action]:
        pass

    def reference_id(self) -> str:
        return self.funds_pull_pre_approval.funds_pre_approval_id

    def new_command(self) -> "Command":
        pass

    def validate(self, prior: typing.Optional["Command"]) -> None:
        pass

    ...
