# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from dataclasses import replace, asdict
from diem.testing.miniwallet import KycSample, Account, PaymentUri, Transaction, PaymentCommand
from diem import offchain


def test_match_kyc_data():
    ks = KycSample.gen("foo")
    obj = offchain.from_json(ks.soft_match, offchain.KycDataObject)
    assert ks.match_kyc_data("soft_match", obj)
    assert not ks.match_kyc_data("reject", obj)

    obj = replace(obj, legal_entity_name="hello")
    assert ks.match_kyc_data("soft_match", obj)

    obj = replace(obj, given_name="hello")
    assert not ks.match_kyc_data("soft_match", obj)


def test_decode_account_kyc_data():
    assert Account(id="1").kyc_data_object() == offchain.individual_kyc_data()

    sample = KycSample.gen("foo")
    account = Account(id="1", kyc_data=sample.minimum)
    assert account.kyc_data_object()
    assert offchain.to_json(account.kyc_data_object()) == sample.minimum


def test_payment_uri_intent_identifier():
    uri = PaymentUri(
        id="1",
        account_id="2",
        payment_uri="diem://dm1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4us2vfufk",
    )
    assert uri.intent("dm")
    assert uri.intent("dm").sub_address.hex() == "cf64428bdeb62af2"


def test_transaction_balance_amount():
    txn = Transaction(id="1", account_id="2", currency="XUS", amount=1000, status=Transaction.Status.pending)
    assert txn.balance_amount() == 1000

    txn.payee = "dm1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4us2vfufk"
    assert txn.balance_amount() == -1000


def test_transaction_subaddress():
    txn = Transaction(id="1", account_id="2", currency="XUS", amount=1000, status=Transaction.Status.pending)
    txn.subaddress_hex = "cf64428bdeb62af2"
    assert txn.subaddress().hex() == "cf64428bdeb62af2"


def test_payment_command_to_offchain_command(factory):
    offchain_cmd = factory.new_sender_payment_command()
    cmd = PaymentCommand(
        id="1",
        account_id="2",
        is_sender=offchain_cmd.is_sender(),
        reference_id=offchain_cmd.reference_id(),
        is_inbound=offchain_cmd.is_inbound(),
        cid=offchain_cmd.id(),
        payment_object=asdict(offchain_cmd.payment),
    )
    assert cmd.to_offchain_command() == offchain_cmd
