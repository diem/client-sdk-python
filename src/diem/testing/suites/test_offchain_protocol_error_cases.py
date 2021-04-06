# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import identifier, jsonrpc, offchain
from diem.testing import LocalAccount
from diem.testing.miniwallet import RestClient, AppConfig
from typing import Dict, Any, Tuple, Optional
import json, time, requests, uuid


def test_invalid_x_request_id(
    stub_config: AppConfig,
    target_client: RestClient,
    stub_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create a valid offchain request object.
    2. Send request to the target wallet application offchain API endpoint with X-Request-ID does not
       match UUID format.
    3. Expect response status code is 400
    4. Expect response `CommandResponseObject` with failure status and error object
    """

    receiver_address = target_client.create_account().generate_account_identifier(hrp)
    sender_address = stub_client.create_account().generate_account_identifier(hrp)
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=json.loads(target_client.new_kyc_data(sample="minimum")),
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    status_code, resp = send_request_json(
        diem_client,
        stub_config.account,
        sender_address,
        receiver_address,
        json.dumps(request),
        hrp,
        x_request_id="invalid uuid",
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "invalid_http_header", "protocol_error")


def send_request_json(
    diem_client: jsonrpc.Client,
    sender_account: LocalAccount,
    sender_address: str,
    receiver_address: str,
    request_json: str,
    hrp: str,
    x_request_id: str = str(uuid.uuid4()),
) -> Tuple[int, offchain.CommandResponseObject]:
    account_address, _ = identifier.decode_account(receiver_address, hrp)
    base_url, public_key = diem_client.get_base_url_and_compliance_key(account_address)
    resp = requests.Session().post(
        f"{base_url.rstrip('/')}/v2/command",
        data=offchain.jws.serialize_string(request_json, sender_account.compliance_key.sign),
        headers={
            offchain.http_header.X_REQUEST_ID: x_request_id,
            offchain.http_header.X_REQUEST_SENDER_ADDRESS: sender_address,
        },
    )

    cmd_resp_obj = offchain.jws.deserialize(resp.content, offchain.CommandResponseObject, public_key.verify)

    return (resp.status_code, cmd_resp_obj)


def payment_command_request_sample(
    sender_address: str, sender_kyc_data: Dict[str, Any], receiver_address: str, currency: str, amount: int
) -> Dict[str, Any]:
    """Creates a `PaymentCommand` initial state request JSON object (dictionary).

    Sender address is from the stub wallet application.

    Receiver address is from the target wallet application.
    """

    return {
        "_ObjectType": "CommandRequestObject",
        "cid": "c77053c9-9c44-4c84-aaf5-aa142eab23fc",
        "command_type": "PaymentCommand",
        "command": {
            "_ObjectType": "PaymentCommand",
            "payment": {
                "reference_id": "18c2006f-f29f-4ec7-b0e1-399505e58aa2",
                "sender": {
                    "address": sender_address,
                    "status": {"status": "needs_kyc_data"},
                    "kyc_data": sender_kyc_data,
                },
                "receiver": {
                    "address": receiver_address,
                    "status": {"status": "none"},
                },
                "action": {
                    "amount": amount,
                    "currency": currency,
                    "action": "charge",
                    "timestamp": int(time.time()),
                },
            },
        },
    }


def assert_response_error(
    resp: offchain.CommandResponseObject, code: str, err_type: str, field: Optional[str] = None
) -> None:
    assert resp.error, resp
    assert resp.error.type == err_type, resp
    assert resp.error.code == code, resp
    assert resp.error.field == field, resp
