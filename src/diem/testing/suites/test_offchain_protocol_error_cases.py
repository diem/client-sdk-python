# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import asdict
from diem import identifier, jsonrpc, offchain, testnet
from diem.testing import LocalAccount
from diem.testing.miniwallet import RestClient, AppConfig
from typing import Dict, Any, Tuple, Optional
import json, time, requests, uuid, pytest


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
    4. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `invalid_http_header` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier(hrp)
    sender_address = stub_client.create_account().generate_account_identifier(hrp)
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.new_kyc_data(sample="minimum"),
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


def test_missing_x_request_id(
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
    2. Send request to the target wallet application offchain API endpoint without X-Request-ID.
    3. Expect response status code is 400
    4. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `missing_http_header` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier(hrp)
    sender_address = stub_client.create_account().generate_account_identifier(hrp)
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.new_kyc_data(sample="minimum"),
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
        x_request_id=None,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "missing_http_header", "protocol_error")


@pytest.mark.parametrize(
    "invalid_sender_address",
    [
        "invalid hex-encoded address",
        "18e97a844979a76b030119db95aaf9d0",
        "xdm1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4us2vfufk",
    ],
)
def test_invalid_x_request_sender_address(
    stub_config: AppConfig,
    target_client: RestClient,
    stub_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
    invalid_sender_address: str,
) -> None:
    """
    Test Plan:

    1. Create a valid offchain request object.
    2. Send request to the target wallet application offchain API endpoint with invalid X-Request-Sender-Address.
    3. Expect response status code is 400
    4. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `invalid_http_header` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier(hrp)
    sender_address = stub_client.create_account().generate_account_identifier(hrp)
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.new_kyc_data(sample="minimum"),
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    status_code, resp = send_request_json(
        diem_client,
        stub_config.account,
        invalid_sender_address,
        receiver_address,
        json.dumps(request),
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "invalid_http_header", "protocol_error")


def test_missing_x_request_sender_address(
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
    2. Send request to the target wallet application offchain API endpoint without X-Request-Sender-Address header.
    3. Expect response status code is 400
    4. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `missing_http_header` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier(hrp)
    sender_address = stub_client.create_account().generate_account_identifier(hrp)
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.new_kyc_data(sample="minimum"),
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    status_code, resp = send_request_json(
        diem_client,
        stub_config.account,
        None,
        receiver_address,
        json.dumps(request),
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "missing_http_header", "protocol_error")


def test_x_request_sender_is_valid_but_no_compliance_key(
    target_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create a new on-chain account without base_url and compliance key.
    2. Use new on-chain account address as sender address to create payment command request.
    3. Send request to the target wallet application offchain API endpoint with new on-chain account address.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `invalid_http_header` error code.
    """

    new_stub_account = testnet.gen_account(diem_client)
    receiver_address = target_client.create_account().generate_account_identifier(hrp)
    sender_address = new_stub_account.account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.new_kyc_data(sample="minimum"),
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    status_code, resp = send_request_json(
        diem_client,
        new_stub_account,
        sender_address,
        receiver_address,
        json.dumps(request),
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "invalid_http_header", "protocol_error")


def test_invalid_jws_message_body_that_misses_parts(
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

    1. Create a new on-chain account with base_url and compliance key.
    2. Use new on-chain account address as sender address to create payment command request.
    3. Send request that missed jws header part to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `invalid_jws` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier(hrp)
    sender_address = stub_client.create_account().generate_account_identifier(hrp)
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.new_kyc_data(sample="minimum"),
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
        request_body=b"invalid.jws_msg",
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "invalid_jws", "protocol_error")


def test_invalid_jws_message_signature(
    stub_config: AppConfig,
    target_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create a new on-chain account with base_url and a new compliance key.
    2. Use new on-chain account address as sender address to create payment command request.
    3. Send request to the target wallet application offchain API endpoint with new on-chain account address and a different compliance key.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `invalid_jws_signature` error code.
    """

    new_stub_account = testnet.gen_account(diem_client)
    new_compliance_key = LocalAccount().compliance_public_key_bytes
    new_stub_account.rotate_dual_attestation_info(diem_client, stub_config.server_url, new_compliance_key)

    receiver_address = target_client.create_account().generate_account_identifier(hrp)
    sender_address = new_stub_account.account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.new_kyc_data(sample="minimum"),
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )

    status_code, resp = send_request_json(
        diem_client,
        new_stub_account,
        sender_address,
        receiver_address,
        json.dumps(request),
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "invalid_jws_signature", "protocol_error")


def send_request_json(
    diem_client: jsonrpc.Client,
    sender_account: LocalAccount,
    sender_address: Optional[str],
    receiver_address: str,
    request_json: str,
    hrp: str,
    x_request_id: Optional[str] = str(uuid.uuid4()),
    request_body: Optional[bytes] = None,
) -> Tuple[int, offchain.CommandResponseObject]:
    headers = {}
    if x_request_id:
        headers[offchain.http_header.X_REQUEST_ID] = x_request_id
    if sender_address:
        headers[offchain.http_header.X_REQUEST_SENDER_ADDRESS] = sender_address

    account_address, _ = identifier.decode_account(receiver_address, hrp)
    base_url, public_key = diem_client.get_base_url_and_compliance_key(account_address)
    if request_body is None:
        request_body = offchain.jws.serialize_string(request_json, sender_account.compliance_key.sign)
    resp = requests.Session().post(
        f"{base_url.rstrip('/')}/v2/command",
        data=request_body,
        headers=headers,
    )

    cmd_resp_obj = offchain.jws.deserialize(resp.content, offchain.CommandResponseObject, public_key.verify)

    return (resp.status_code, cmd_resp_obj)


def payment_command_request_sample(
    sender_address: str, sender_kyc_data: offchain.KycDataObject, receiver_address: str, currency: str, amount: int
) -> Dict[str, Any]:
    """Creates a `PaymentCommand` initial state request JSON object (dictionary).

    Sender address is from the stub wallet application.

    Receiver address is from the target wallet application.
    """

    return {
        "_ObjectType": "CommandRequestObject",
        "cid": str(uuid.uuid4()),
        "command_type": "PaymentCommand",
        "command": {
            "_ObjectType": "PaymentCommand",
            "payment": {
                "reference_id": str(uuid.uuid4()),
                "sender": {
                    "address": sender_address,
                    "status": {"status": "needs_kyc_data"},
                    "kyc_data": asdict(sender_kyc_data),
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
