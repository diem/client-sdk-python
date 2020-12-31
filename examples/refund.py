# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import (
    identifier,
    stdlib,
    testnet,
    txnmetadata,
    utils,
)

from .stubs import CustodialApp


def test_refund_transaction_of_custodial_to_custodial_under_threshold():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    sender_custodial = CustodialApp.create(faucet.gen_account(), client)
    receiver_custodial = CustodialApp.create(faucet.gen_account(), client)

    # create a payment transaction
    intent_id = receiver_custodial.payment(user_id=0, amount=1_000_000)
    intent = identifier.decode_intent(intent_id, identifier.TDM)

    receiver_address = utils.account_address(intent.account_address)
    script = stdlib.encode_peer_to_peer_with_metadata_script(
        currency=utils.currency_code(intent.currency_code),
        payee=receiver_address,
        amount=intent.amount,
        metadata=txnmetadata.general_metadata(sender_custodial.find_user_sub_address_by_id(0), intent.sub_address),
        metadata_signature=b"",  # only travel rule metadata requires signature
    )

    sender = sender_custodial.available_child_vasp()
    txn = sender_custodial.create_transaction(sender, script, intent.currency_code)

    signed_txn = sender.sign(txn)
    client.submit(signed_txn)
    executed_txn = client.wait_for_transaction(signed_txn)

    # start to refund the transaction

    # find the event for the receiver, a p2p transaction may contains multiple receivers
    # in the future.
    event = txnmetadata.find_refund_reference_event(executed_txn, receiver_address)
    assert event is not None
    amount = event.data.amount.amount
    currency_code = event.data.amount.currency
    refund_receiver_address = utils.account_address(event.data.sender)

    metadata = txnmetadata.refund_metadata_from_event(event)
    refund_txn_script = stdlib.encode_peer_to_peer_with_metadata_script(
        currency=utils.currency_code(currency_code),
        payee=refund_receiver_address,
        amount=amount,
        metadata=metadata,
        metadata_signature=b"",  # only travel rule metadata requires signature
    )

    # receiver is sender of refund txn
    sender = receiver_custodial.available_child_vasp()
    txn = receiver_custodial.create_transaction(sender, refund_txn_script, currency_code)
    refund_executed_txn = receiver_custodial.submit_and_wait(sender.sign(txn))
    assert refund_executed_txn is not None
