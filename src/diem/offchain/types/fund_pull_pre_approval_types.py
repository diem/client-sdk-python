import typing

from dataclasses import dataclass, field as datafield

from .command_types import CommandType


class FundPullPreApprovalStatus:
    # Pending user/VASP approval
    pending = "pending"
    # Approved by the user/VASP and ready for use
    valid = "valid"
    # User/VASP did not approve the pre-approval request
    rejected = "rejected"
    # Approval has been closed by the user/VASP and can no longer be used
    closed = "closed"


class TimeUnit:
    day = "day"
    week = "week"
    month = "month"
    year = "year"


@dataclass(frozen=True)
class CurrencyObject:
    amount: int
    currency: str


@dataclass(frozen=True)
class ScopedCumulativeAmountObject:
    unit: str = datafield(metadata={"valid-values": [TimeUnit.day, TimeUnit.week, TimeUnit.month, TimeUnit.year]})
    value: int
    max_amount: CurrencyObject


class FundPullPreApprovalType:
    save_sub_account = "save_sub_account"
    consent = "consent"


@dataclass(frozen=True)
class FundPullPreApprovalScopeObject:
    type: str = datafield(
        metadata={"valid-values": [FundPullPreApprovalType.save_sub_account, FundPullPreApprovalType.consent]}
    )
    expiration_timestamp: int
    max_cumulative_amount: typing.Optional[ScopedCumulativeAmountObject] = datafield(default=None)
    max_transaction_amount: typing.Optional[CurrencyObject] = datafield(default=None)


@dataclass(frozen=True)
class FundPullPreApprovalObject:
    funds_pull_pre_approval_id: str = datafield(metadata={"write_once": True})
    address: str = datafield(metadata={"write_once": True})
    biller_address: str = datafield(metadata={"write_once": True})
    scope: FundPullPreApprovalScopeObject
    status: str = datafield(
        metadata={
            "valid-values": [
                FundPullPreApprovalStatus.pending,
                FundPullPreApprovalStatus.valid,
                FundPullPreApprovalStatus.rejected,
                FundPullPreApprovalStatus.closed,
            ]
        }
    )
    description: typing.Optional[str] = datafield(default=None)


@dataclass(frozen=True)
class FundPullPreApprovalCommandObject:
    fund_pull_pre_approval: FundPullPreApprovalObject
    _ObjectType: str = datafield(
        default=CommandType.FundPullPreApprovalCommand,
        metadata={"valid-values": [CommandType.FundPullPreApprovalCommand]},
    )
