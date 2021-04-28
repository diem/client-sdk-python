# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import jsonrpc, testnet
from diem.testing import LocalAccount
from diem.testing.miniwallet import RestClient, AppConfig
from .conftest import assert_response_error, payment_command_request_sample, send_request_json
import json, pytest


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

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
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

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
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

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
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

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
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
    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = new_stub_account.account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
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

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
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
    new_stub_account.hrp = hrp
    new_compliance_key = LocalAccount().compliance_public_key_bytes
    new_stub_account.rotate_dual_attestation_info(diem_client, stub_config.server_url, new_compliance_key)

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = new_stub_account.account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
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


def test_decoded_jws_message_body_is_not_json_encoded_string(
    stub_config: AppConfig,
    stub_client: RestClient,
    target_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Send request to the target wallet application offchain API endpoint with text "hello world"
    2. Expect response status code is 400
    3. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `invalid_json` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    status_code, resp = send_request_json(
        diem_client,
        stub_config.account,
        sender_address,
        receiver_address,
        "hello world",
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "invalid_json", "protocol_error")


@pytest.mark.parametrize("field_name", ["_ObjectType", "cid", "command_type"])
def test_decoded_command_request_object_missing_required_field(
    stub_config: AppConfig,
    stub_client: RestClient,
    target_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
    field_name: str,
) -> None:
    """
    Test Plan:

    1. Create a valid offchain request object.
    2. Remove a required field by name defined by the test
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `missing_field` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    del request[field_name]

    status_code, resp = send_request_json(
        diem_client,
        stub_config.account,
        sender_address,
        receiver_address,
        json.dumps(request),
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "missing_field", "protocol_error", field=field_name)


@pytest.mark.parametrize("field_name", ["_ObjectType", "cid"])
def test_decoded_command_request_object_field_value_is_invalid(
    stub_config: AppConfig,
    stub_client: RestClient,
    target_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
    field_name: str,
) -> None:
    """
    Test Plan:

    1. Create a valid offchain request object.
    2. Set a field value to "invalid value".
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `invalid_field_value` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    request[field_name] = "invalid value"

    status_code, resp = send_request_json(
        diem_client,
        stub_config.account,
        sender_address,
        receiver_address,
        json.dumps(request),
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "invalid_field_value", "protocol_error", field=field_name)


def test_decoded_command_request_object_command_type_is_unknown(
    stub_config: AppConfig,
    stub_client: RestClient,
    target_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
) -> None:
    """
    Test Plan:

    1. Create a valid offchain request object.
    2. Set request command_type to "AbcCommand"
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `unknown_command_type` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    request["command_type"] = "AbcCommand"

    status_code, resp = send_request_json(
        diem_client,
        stub_config.account,
        sender_address,
        receiver_address,
        json.dumps(request),
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert resp.cid == request["cid"]
    assert_response_error(resp, "unknown_command_type", "protocol_error", field="command_type")


@pytest.mark.parametrize("field_name", ["_ObjectType", "cid", "command_type"])
def test_decoded_command_request_object_field_value_type_is_invalid(
    stub_config: AppConfig,
    stub_client: RestClient,
    target_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
    field_name: str,
) -> None:
    """
    Test Plan:

    1. Create a valid offchain request object.
    2. Set a field value to boolean type True.
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `protocol_error` error type,
       and `invalid_field_value` error code.
    """

    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.get_kyc_sample().minimum,
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    request[field_name] = True

    status_code, resp = send_request_json(
        diem_client,
        stub_config.account,
        sender_address,
        receiver_address,
        json.dumps(request),
        hrp,
    )
    assert status_code == 400
    assert resp.status == "failure"
    assert_response_error(resp, "invalid_field_value", "protocol_error", field=field_name)
