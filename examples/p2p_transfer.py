# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time

from diem import (
    identifier,
    diem_types,
    stdlib,
    testnet,
    txnmetadata,
    utils,
)

from .stubs import CustodialApp


async def test_custodial_to_custodial_under_threshold():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    sender_account = await faucet.gen_account()
    sender_custodial = CustodialApp.create(sender_account, client)
    receiver_account = await faucet.gen_account()
    receiver_custodial = CustodialApp.create(receiver_account, client)

    intent_id = receiver_custodial.payment(user_id=0, amount=1_000_000)

    intent = identifier.decode_intent(intent_id, identifier.TDM)

    script = stdlib.encode_peer_to_peer_with_metadata_script(
        currency=utils.currency_code(intent.currency_code),
        payee=utils.account_address(intent.account_address),
        amount=intent.amount,
        metadata=txnmetadata.general_metadata(sender_custodial.find_user_sub_address_by_id(0), intent.sub_address),
        metadata_signature=b"",  # only travel rule metadata requires signature
    )

    sender = sender_custodial.available_child_vasp()
    seq_num = await client.get_account_sequence(sender.account_address)
    txn = create_transaction(sender, seq_num, script, intent.currency_code)

    signed_txn = sender.sign(txn)
    await client.submit(signed_txn)
    executed_txn = await client.wait_for_transaction(signed_txn)
    assert executed_txn is not None


async def test_custodial_to_custodial_above_threshold():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    sender_account = await faucet.gen_account()
    sender_custodial = CustodialApp.create(sender_account, client)
    receiver_account = await faucet.gen_account()
    receiver_custodial = CustodialApp.create(receiver_account, client)
    receiver_custodial.init_compliance_keys()

    intent_id = receiver_custodial.payment(user_id=0, amount=2_000_000_000)

    intent = identifier.decode_intent(intent_id, identifier.TDM)

    sender = sender_custodial.available_child_vasp()
    # sender & receiver communicate by off chain APIs
    off_chain_reference_id = "32323abc"
    metadata, metadata_signing_msg = txnmetadata.travel_rule(
        off_chain_reference_id, sender.account_address, intent.amount
    )
    metadata_signature = receiver_custodial.compliance_key.sign(metadata_signing_msg)

    # sender constructs transaction after off chain communication
    script = stdlib.encode_peer_to_peer_with_metadata_script(
        currency=utils.currency_code(intent.currency_code),
        payee=utils.account_address(intent.account_address),
        amount=intent.amount,
        metadata=metadata,
        metadata_signature=metadata_signature,
    )

    seq_num = await client.get_account_sequence(sender.account_address)
    txn = create_transaction(sender, seq_num, script, intent.currency_code)

    signed_txn = sender.sign(txn)
    await client.submit(signed_txn)
    executed_txn = await client.wait_for_transaction(signed_txn)
    assert executed_txn is not None


def create_transaction(sender, sender_account_sequence, script, currency):
    return diem_types.RawTransaction(
        sender=sender.account_address,
        sequence_number=sender_account_sequence,
        payload=diem_types.TransactionPayload__Script(script),
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code=currency,
        expiration_timestamp_secs=int(time.time()) + 30,
        chain_id=testnet.CHAIN_ID,
    )
