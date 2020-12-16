# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from enum import Enum


class Action(Enum):
    EVALUATE_KYC_DATA = "evaluate_kyc_data"
    REVIEW_KYC_DATA = "review_kyc_data"
    CLEAR_SOFT_MATCH = "clear_soft_match"
    SUBMIT_TXN = "submit_transaction"
