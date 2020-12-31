# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain, identifier, txnmetadata
from dataclasses import replace

import pytest


def test_is_both_ready(factory):
    cmd = factory.new_sender_payment_command()
    assert not cmd.is_both_ready()
    cmd = cmd.new_command(status=offchain.Status.ready_for_settlement)
    assert not cmd.is_both_ready()

    cmd = replace(cmd, my_actor_address=cmd.payment.receiver.address)
    cmd = cmd.new_command(status=offchain.Status.ready_for_settlement)
    assert cmd.is_both_ready()


def test_is_abort(factory):
    cmd = factory.new_sender_payment_command()
    assert not cmd.is_abort()
    cmd = cmd.new_command(status=offchain.Status.abort)
    assert cmd.is_abort()

    cmd = cmd.new_command(status=offchain.Status.ready_for_settlement)
    assert not cmd.is_abort()

    cmd = replace(cmd, my_actor_address=cmd.payment.receiver.address)
    cmd = cmd.new_command(status=offchain.Status.abort)
    assert cmd.is_abort()


def test_receiver_addresses(factory):
    cmd = factory.new_sender_payment_command()
    account_address, subaddress = identifier.decode_account(cmd.payment.receiver.address, factory.hrp())
    assert account_address == cmd.receiver_account_address(factory.hrp())
    assert subaddress == cmd.receiver_subaddress(factory.hrp())


def test_sender_addresses(factory):
    cmd = factory.new_sender_payment_command()
    account_address, subaddress = identifier.decode_account(cmd.payment.sender.address, factory.hrp())
    assert account_address == cmd.sender_account_address(factory.hrp())
    assert subaddress == cmd.sender_subaddress(factory.hrp())


def test_travel_rule_metadata_and_sig_message(factory):
    cmd = factory.new_sender_payment_command()
    metadata, sig_msg = txnmetadata.travel_rule(
        cmd.payment.reference_id, cmd.sender_account_address(factory.hrp()), cmd.payment.action.amount
    )

    assert metadata == cmd.travel_rule_metadata(factory.hrp())
    assert sig_msg == cmd.travel_rule_metadata_signature_message(factory.hrp())


def test_to_json(factory):
    cmd = factory.new_sender_payment_command()
    assert cmd == offchain.from_json(offchain.to_json(cmd), offchain.PaymentCommand)


def test_new_command_with_metadata_should_append_to_existing_metadata(factory):
    cmd = factory.new_sender_payment_command()
    cmd = cmd.new_command(metadata=["hello"])
    cmd = cmd.new_command(metadata=["world"])
    assert cmd.payment.receiver.metadata is None
    assert cmd.payment.sender.metadata == ["hello", "world"]


def test_new_command_raises_value_error_if_metadata_is_not_list(factory):
    cmd = factory.new_sender_payment_command()
    with pytest.raises(ValueError):
        cmd.new_command(metadata="hello")
