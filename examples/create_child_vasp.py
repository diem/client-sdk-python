# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


import time

from diem import (
    diem_types,
    stdlib,
    testnet,
    utils,
    LocalAccount,
)


def test_create_child_vasp():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    parent_vasp = faucet.gen_account()
    seq_num = client.get_account_sequence(parent_vasp.account_address)

    child_vasp = LocalAccount.generate()
    currency = testnet.TEST_CURRENCY_CODE
    raw_txn = diem_types.RawTransaction(
        sender=parent_vasp.account_address,
        sequence_number=seq_num,
        payload=diem_types.TransactionPayload__Script(
            stdlib.encode_create_child_vasp_account_script(
                coin_type=utils.currency_code(currency),
                child_address=child_vasp.account_address,
                auth_key_prefix=child_vasp.auth_key.prefix(),
                add_all_currencies=False,
                child_initial_balance=100_000_000,
            )
        ),
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code=currency,
        expiration_timestamp_secs=int(time.time()) + 30,
        chain_id=testnet.CHAIN_ID,
    )
    txn = parent_vasp.sign(raw_txn)
    client.submit(txn)
    executed_txn = client.wait_for_transaction(txn)
    assert executed_txn is not None
