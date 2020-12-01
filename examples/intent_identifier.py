# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


import secrets

from diem import identifier, utils, LocalAccount


def test_intent_identifier():
    child_vasp_address = "d738a0b9851305dfe1d17707f0841dbc"
    user_sub_address = "9072d012034a880f"
    currency_code = "Coin1"
    amount = 10_000_000

    account_id = identifier.encode_account(
        child_vasp_address, utils.sub_address(user_sub_address), identifier.TLB  # testnet HRP
    )
    intent_id = identifier.encode_intent(account_id, currency_code, amount)

    assert intent_id == "diem://tlb1p6uu2pwv9zvzalcw3wurlppqahjg895qjqd9gsrc5pe4ul?c=Coin1&am=10000000"
