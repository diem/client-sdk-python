# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time, secrets, typing

from libra import (
    identifier,
    jsonrpc,
    libra_types,
    stdlib,
    testnet,
    txnmetadata,
    utils,
    LocalAccount,
)

from .stubs import CustodialApp


def test_non_custodial_to_non_custodial():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    sender = faucet.gen_account()
    receiver = faucet.gen_account()

    amount = 1_000_000

    script = stdlib.encode_peer_to_peer_with_metadata_script(
        currency=utils.currency_code("LBR"),
        payee=receiver.account_address,
        amount=amount,
        metadata=b'', # no requirement for metadata and metadata signature
        metadata_signature=b'',
    )
    txn = create_transaction(sender, client.get_account_sequence(sender.account_address), script)

    signed_txn = sender.sign(txn)
    client.submit(signed_txn)
    executed_txn = client.wait_for_transaction(signed_txn)
    assert executed_txn is not None


def test_non_custodial_to_custodial():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    sender = faucet.gen_account()
    receiver_custodial = CustodialApp.create(faucet.gen_account())
    intent_id = receiver_custodial.payment(user_id=0, amount=1_000_000)

    receiver_account_id, currency, amount = identifier.decode_intent(intent_id)
    receiver_address, sub_address = identifier.decode_account(receiver_account_id)

    script = stdlib.encode_peer_to_peer_with_metadata_script(
        currency=utils.currency_code(currency),
        payee=utils.account_address(receiver_address),
        amount=amount,
        metadata=txnmetadata.general_metadata(None, utils.sub_address(sub_address)),
        metadata_signature=b'', # only travel rule metadata requires signature
    )
    txn = create_transaction(sender, client.get_account_sequence(sender.account_address), script, currency)

    signed_txn = sender.sign(txn)
    client.submit(signed_txn)
    executed_txn = client.wait_for_transaction(signed_txn)
    assert executed_txn is not None



def create_transaction(sender, sender_account_sequence, script, currency="LBR"):
    return libra_types.RawTransaction(
        sender=sender.account_address,
        sequence_number=sender_account_sequence,
        payload=libra_types.TransactionPayload__Script(script),
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code=currency,
        expiration_timestamp_secs=int(time.time()) + 30,
        chain_id=testnet.CHAIN_ID,
    )
