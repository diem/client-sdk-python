# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import (
    identifier,
    diem_types,
    stdlib,
    chain_ids,
    txnmetadata,
    utils,
)
from diem.testing import create_client, Faucet, XUS
import pytest, time, uuid


@pytest.mark.asyncio
async def test_p2p_under_threshold_by_subaddress():
    client = create_client()
    faucet = Faucet(client)

    sender = await faucet.gen_account()
    sender_subaddress = identifier.gen_subaddress()
    receiver = await faucet.gen_account()
    receiver_subaddress = identifier.gen_subaddress()

    amount = 2_000_000

    payload = stdlib.encode_peer_to_peer_with_metadata_script_function(
        currency=utils.currency_code(XUS),
        payee=receiver.account_address,
        amount=amount,
        metadata=txnmetadata.general_metadata(sender_subaddress, receiver_subaddress),
        metadata_signature=b"",  # only travel rule metadata requires signature
    )

    seq_num = await client.get_account_sequence(sender.account_address)
    txn = diem_types.RawTransaction(
        sender=sender.account_address,
        sequence_number=seq_num,
        payload=payload,
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code=XUS,
        expiration_timestamp_secs=int(time.time()) + 30,
        chain_id=chain_ids.TESTNET,
    )

    signed_txn = sender.sign(txn)
    await client.submit(signed_txn)
    executed_txn = await client.wait_for_transaction(signed_txn)
    assert executed_txn is not None


@pytest.mark.asyncio
async def test_p2p_above_threshold_by_reference_id():
    client = create_client()
    faucet = Faucet(client)

    sender = await faucet.gen_account()
    receiver = await faucet.gen_account()
    await receiver.rotate_dual_attestation_info(client, base_url="http://localhost")

    amount = 20_000_000_000
    reference_id = str(uuid.uuid4())

    metadata, metadata_signing_msg = txnmetadata.travel_rule(reference_id, sender.account_address, amount)
    metadata_signature = receiver.compliance_key.sign(metadata_signing_msg)
    payload = stdlib.encode_peer_to_peer_with_metadata_script_function(
        currency=utils.currency_code(XUS),
        payee=receiver.account_address,
        amount=amount,
        metadata=metadata,
        metadata_signature=metadata_signature,
    )

    seq_num = await client.get_account_sequence(sender.account_address)
    txn = diem_types.RawTransaction(
        sender=sender.account_address,
        sequence_number=seq_num,
        payload=payload,
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code=XUS,
        expiration_timestamp_secs=int(time.time()) + 30,
        chain_id=chain_ids.TESTNET,
    )

    signed_txn = sender.sign(txn)
    await client.submit(signed_txn)
    executed_txn = await client.wait_for_transaction(signed_txn)
    assert executed_txn is not None
