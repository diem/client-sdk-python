# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import typing

from .types import FundPullPreApprovalStatus

Status = str

_transitions: typing.Dict[Status, typing.List[Status]] = {
    FundPullPreApprovalStatus.pending: [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.closed,
    ],
    FundPullPreApprovalStatus.valid: [
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.closed,
    ],
    FundPullPreApprovalStatus.rejected: [
        FundPullPreApprovalStatus.rejected,
    ],
    FundPullPreApprovalStatus.closed: [
        FundPullPreApprovalStatus.closed,
    ],
}

_initial_states: typing.List[Status] = [
    FundPullPreApprovalStatus.pending,
    FundPullPreApprovalStatus.valid,
    FundPullPreApprovalStatus.rejected,
]


def is_valid_transition(current_status: Status, next_status: Status) -> bool:
    return next_status in _transitions[current_status]


def is_valid_initial_status(status: Status) -> bool:
    return status in _initial_states
