# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain, testnet


def test_send_and_deserialize_request(factory):
    client = testnet.create_client()
    receiver_port = offchain.http_server.get_available_port()
    sender = testnet.gen_account(client, base_url="http://localhost:8888")
    receiver = testnet.gen_account(client, base_url=f"http://localhost:{receiver_port}")
    sender_client = factory.create_offchain_client(sender, client)
    receiver_client = factory.create_offchain_client(receiver, client)

    def process_inbound_request(x_request_id: str, jws_key_address: str, content: bytes):
        command = receiver_client.process_inbound_request(jws_key_address, content)
        resp = offchain.reply_request(command.id())
        return (200, offchain.jws.serialize(resp, receiver.compliance_key.sign))

    offchain.http_server.start_local(receiver_port, process_inbound_request)

    payment = factory.new_payment_object(sender, receiver)
    command = offchain.PaymentCommand(payment=payment, my_actor_address=payment.sender.address, inbound=False)
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
