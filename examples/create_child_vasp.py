# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import (
    diem_types,
    stdlib,
    chain_ids,
    utils,
)
from diem.testing import LocalAccount, create_client, Faucet, XUS
import pytest, time


@pytest.mark.asyncio
async def test_create_child_vasp():
    client = create_client()
    faucet = Faucet(client)

    parent_vasp = await faucet.gen_account()
    seq_num = await client.get_account_sequence(parent_vasp.account_address)

    child_vasp = LocalAccount.generate()
    payload = stdlib.encode_create_child_vasp_account_script_function(
        coin_type=utils.currency_code(XUS),
        child_address=child_vasp.account_address,
        auth_key_prefix=child_vasp.auth_key.prefix(),
        add_all_currencies=False,
        child_initial_balance=100_000_000,
    )
    raw_txn = diem_types.RawTransaction(
        sender=parent_vasp.account_address,
        sequence_number=seq_num,
        payload=payload,
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code=XUS,
        expiration_timestamp_secs=int(time.time()) + 30,
        chain_id=chain_ids.TESTNET,
    )
    txn = parent_vasp.sign(raw_txn)
    await client.submit(txn)
    executed_txn = await client.wait_for_transaction(txn)
    assert executed_txn is not None
