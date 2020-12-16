# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain, testnet


def test_send_and_deserialize_request(factory):
    client = testnet.create_client()
    receiver_port = offchain.http_server.get_available_port()
    sender = testnet.gen_vasp_account(client, "http://localhost:8888")
    receiver = testnet.gen_vasp_account(client, f"http://localhost:{receiver_port}")
    sender_client = factory.create_offchain_client(sender, client)
    receiver_client = factory.create_offchain_client(receiver, client)

    def process_inbound_request(x_request_id: str, jws_key_address: str, content: bytes):
        command = receiver_client.process_inbound_request(jws_key_address, content)
        resp = offchain.reply_request(command.cid)
        return (200, offchain.jws.serialize(resp, receiver.compliance_key.sign))

    offchain.http_server.start_local(receiver_port, process_inbound_request)

    payment = factory.new_payment_object(sender, receiver)
    command = offchain.PaymentCommand(payment=payment, my_actor_address=payment.sender.address, inbound=False)
    resp = sender_client.send_command(command, sender.compliance_key.sign)
    assert resp
