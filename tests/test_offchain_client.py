# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest

from diem import offchain, testnet


@pytest.fixture(params=[offchain.CommandType.PaymentCommand, offchain.CommandType.FundPullPreApprovalCommand])
def command_type(request):
    return request.param


def test_send_and_deserialize_request(factory, command_type):
    client = testnet.create_client()
    receiver_port = offchain.http_server.get_available_port()
    sender = testnet.gen_account(client, base_url="http://localhost:8888")
    receiver = testnet.gen_account(client, base_url=f"http://localhost:{receiver_port}")
    sender_client = factory.create_offchain_client(sender, client)
    receiver_client = factory.create_offchain_client(receiver, client)

    def process_inbound_request(_, jws_key_address: str, content: bytes):
        command = receiver_client.process_inbound_request(jws_key_address, content)
        resp = offchain.reply_request(command.id())
        return 200, offchain.jws.serialize(resp, receiver.compliance_key.sign)

    offchain.http_server.start_local(receiver_port, process_inbound_request)

    command = factory.new_command(command_type, sender, receiver)
    resp = sender_client.send_command(command, sender.compliance_key.sign)
    assert resp


def test_is_under_the_threshold():
    assert offchain.client._is_under_the_threshold(2, 0.2, 1)
    assert offchain.client._is_under_the_threshold(2, 0.2, 5)
    assert not offchain.client._is_under_the_threshold(2, 0.2, 6)
    assert not offchain.client._is_under_the_threshold(2, 0.2, 10)


def test_filter_supported_currency_codes():
    assert ["XUS", "XDX"] == offchain.client._filter_supported_currency_codes(None, ["XUS", "XDX"])
    assert ["XUS"] == offchain.client._filter_supported_currency_codes(["XUS"], ["XUS", "XDX"])
    assert ["XDX"] == offchain.client._filter_supported_currency_codes(None, ["XDX"])
    assert [] == offchain.client._filter_supported_currency_codes(["XUS"], ["XDX"])


def test_incoming_payment_command_type_mismatch(factory):
    client = testnet.create_client()
    receiver_port = offchain.http_server.get_available_port()
    sender = testnet.gen_account(client, base_url="http://localhost:8888")
    receiver = testnet.gen_account(client, base_url=f"http://localhost:{receiver_port}")
    receiver_client = factory.create_offchain_client(receiver, client)

    command = factory.new_command(offchain.CommandType.PaymentCommand, sender, receiver)

    # Use wrong command type to cause a mismatch
    wrong_type = offchain.CommandType.FundPullPreApprovalCommand

    request = offchain.CommandRequestObject(
        cid=command.id(),
        command_type=wrong_type,
        command=offchain.PaymentCommandObject(
            _ObjectType=offchain.CommandType.PaymentCommand,
            payment=command.payment,
        ),
    )
    request_bytes = offchain.jws.serialize(request, sender.compliance_key.sign)

    with pytest.raises(AttributeError, match="fund_pull_pre_approval"):
        receiver_client.process_inbound_request(command.my_address(), request_bytes)


def test_incoming_fppa_command_type_mismatch(factory):
    client = testnet.create_client()
    receiver_port = offchain.http_server.get_available_port()
    sender = testnet.gen_account(client, base_url="http://localhost:8888")
    receiver = testnet.gen_account(client, base_url=f"http://localhost:{receiver_port}")
    receiver_client = factory.create_offchain_client(receiver, client)

    command = factory.new_command(offchain.CommandType.FundPullPreApprovalCommand, sender, receiver)

    # Use wrong command type to cause a mismatch
    wrong_type = offchain.CommandType.PaymentCommand

    request = offchain.CommandRequestObject(
        cid=command.id(),
        command_type=wrong_type,
        command=offchain.FundPullPreApprovalCommandObject(
            _ObjectType=offchain.CommandType.FundPullPreApprovalCommand,
            fund_pull_pre_approval=command.funds_pull_pre_approval,
        ),
    )
    request_bytes = offchain.jws.serialize(request, sender.compliance_key.sign)

    with pytest.raises(AttributeError, match="payment"):
        receiver_client.process_inbound_request(command.my_address(), request_bytes)
