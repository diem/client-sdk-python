# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
import dataclasses

from diem.offchain import FundsPullPreApprovalCommand, FundPullPreApprovalStatus, Error


def clone_with_status(command: FundsPullPreApprovalCommand, new_status: str) -> FundsPullPreApprovalCommand:
    fppa_object = dataclasses.replace(command.funds_pull_pre_approval, status=new_status)
    return dataclasses.replace(command, funds_pull_pre_approval=fppa_object)


def test_pending(factory):
    fppa = factory.new_funds_pull_pre_approval_command()
    fppa = clone_with_status(fppa, FundPullPreApprovalStatus.pending)
    fppa.validate(None)

    # Idempotent
    fppa.validate(fppa)

    # Can transition to any other status
    for next_status in [
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.closed,
    ]:
        next_command = clone_with_status(fppa, next_status)
        next_command.validate(fppa)


def test_valid(factory):
    fppa = factory.new_funds_pull_pre_approval_command()
    fppa = clone_with_status(fppa, FundPullPreApprovalStatus.valid)
    fppa.validate(None)

    # Idempotent
    fppa.validate(fppa)

    # Valid transitions
    for next_status in [
        FundPullPreApprovalStatus.closed,
    ]:
        next_command = clone_with_status(fppa, next_status)
        next_command.validate(fppa)

    # Invalid transitions
    for next_status in [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.rejected,
    ]:
        next_command = clone_with_status(fppa, next_status)
        with pytest.raises(Error):
            next_command.validate(fppa)


def test_rejected(factory):
    fppa = factory.new_funds_pull_pre_approval_command()
    fppa = clone_with_status(fppa, FundPullPreApprovalStatus.rejected)
    fppa.validate(None)

    # Idempotent
    fppa.validate(fppa)

    # Cannot transition to any other status
    for next_status in [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.closed,
    ]:
        next_command = clone_with_status(fppa, next_status)
        with pytest.raises(Error):
            next_command.validate(fppa)


def test_closed(factory):
    fppa = factory.new_funds_pull_pre_approval_command()
    fppa = clone_with_status(fppa, FundPullPreApprovalStatus.closed)

    # Closed is not an initial state
    with pytest.raises(Error):
        fppa.validate(None)

    # Idempotent
    fppa.validate(fppa)

    # Cannot transition to any other status
    for next_status in [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.rejected,
    ]:
        next_command = clone_with_status(fppa, next_status)
        with pytest.raises(Error):
            next_command.validate(fppa)
