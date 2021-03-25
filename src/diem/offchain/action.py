# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines action enum for flagging what should be follow up action of a `PaymentCommand`

See `diem.offchain.payment_command.PaymentCommand.follow_up_action` for more details.
"""

from enum import Enum


class Action(Enum):
    """Action for following up a PaymentCommand

    List of actions for different PaymentCommand status.
    """

    EVALUATE_KYC_DATA = "evaluate_kyc_data"
    REVIEW_KYC_DATA = "review_kyc_data"
    CLEAR_SOFT_MATCH = "clear_soft_match"
    SUBMIT_TXN = "submit_transaction"
