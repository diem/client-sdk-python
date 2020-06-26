# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pylibra

api = pylibra.LibraNetwork()

ASSOC_ADDRESS: str = "000000000000000000000000000000000000000000000000000000000a550c18"

account = api.getAccount(ASSOC_ADDRESS)
print("Account Balance:", account.balance, "Sequence:", account.sequence)
total = 0
seq = 0
while seq < min(account.sequence, 10):
    tx, events = api.transaction_by_acc_seq(ASSOC_ADDRESS, seq=seq, include_events=True)
    if tx.is_mint:
        print("Found mint transcation: from: ", tx.sender.hex())
        total = total + tx.amount
        print("New Total:", total)
    seq = seq + 1
print("minted total:", total)
