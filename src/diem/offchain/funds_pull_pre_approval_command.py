# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import typing
import uuid

from . import FundPullPreApprovalObject, CommandType, new_funds_pull_pre_approval_object
from .command import Command
from .payment_state import Action


@dataclasses.dataclass(frozen=True)
class FundsPullPreApprovalCommand(Command):
    funds_pull_pre_approval: FundPullPreApprovalObject
    cid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    @staticmethod
    def init(
        address: str,
        biller_address: str,
        funds_pull_pre_approval_type: str,
        expiration_timestamp: int,
        status: str,
        max_cumulative_unit: typing.Optional[str] = None,
        max_cumulative_unit_value: typing.Optional[int] = None,
        max_cumulative_amount: typing.Optional[int] = None,
        max_cumulative_amount_currency: typing.Optional[str] = None,
        max_transaction_amount: typing.Optional[int] = None,
        max_transaction_amount_currency: typing.Optional[str] = None,
        description: typing.Optional[str] = None,
    ) -> "FundsPullPreApprovalCommand":
        return FundsPullPreApprovalCommand(
            funds_pull_pre_approval=new_funds_pull_pre_approval_object(
                address=address,
                biller_address=biller_address,
                funds_pull_pre_approval_type=funds_pull_pre_approval_type,
                expiration_timestamp=expiration_timestamp,
                status=status,
                max_cumulative_unit=max_cumulative_unit,
                max_cumulative_unit_value=max_cumulative_unit_value,
                max_cumulative_amount=max_cumulative_amount,
                max_cumulative_amount_currency=max_cumulative_amount_currency,
                max_transaction_amount=max_transaction_amount,
                max_transaction_amount_currency=max_transaction_amount_currency,
                description=description,
            )
        )

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

    def my_address(self):
        return self.my_actor_address

    def opponent_address(self):
        return (
            self.funds_pull_pre_approval.address
            if self.my_actor_address == self.funds_pull_pre_approval.biller_address
            else self.funds_pull_pre_approval.address
        )

    def new_request(self):
        return new_funds_pull_pre_approval_request(funds_pull_pre_approval=self.funds_pull_pre_approval, cid=self.cid)
