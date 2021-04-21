# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import jsonrpc
from diem.testing.miniwallet import RestClient, AppConfig
from typing import Union, List
from .conftest import set_field, assert_response_error, payment_command_request_sample, send_request_json
import json, pytest


@pytest.mark.parametrize(
    "field_name",
    [
        "_ObjectType",
        "payment",
        "payment.sender",
        "payment.sender.address",
        "payment.sender.status",
        "payment.sender.status.status",
        "payment.receiver",
        "payment.receiver.address",
        "payment.receiver.status",
        "payment.receiver.status.status",
        "payment.reference_id",
        "payment.action",
        "payment.action.amount",
        "payment.action.currency",
        "payment.action.action",
        "payment.action.timestamp",
    ],
)
def test_payment_command_contains_missing_required_field(
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

    1. Create a valid offchain PaymentCommand request object.
    2. Set a required field value to None by name defined by the test.
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `missing_field` error code.
    """

    assert_payment_command_field_error(
        stub_config,
        stub_client,
        target_client,
        diem_client,
        currency,
        travel_rule_threshold,
        hrp,
        field_name,
        field_value=None,
        error_code="missing_field",
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "unknown",
        "payment.unknown",
        "payment.sender.unknown",
        "payment.sender.kyc_data.unknown",
        "payment.sender.status.unknown",
        "payment.receiver.unknown",
        "payment.receiver.status.unknown",
        "payment.action.unknown",
    ],
)
def test_payment_command_contains_unknown_field(
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

    1. Create a valid offchain PaymentCommand request object.
    2. Add an unknown field by name defined by the test.
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `unknown_field` error code.
    """

    assert_payment_command_field_error(
        stub_config,
        stub_client,
        target_client,
        diem_client,
        currency,
        travel_rule_threshold,
        hrp,
        field_name,
        field_value="something",
        error_code="unknown_field",
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "_ObjectType",
        "payment.sender.address",
        "payment.sender.status.status",
        "payment.receiver.address",
        "payment.receiver.status.status",
        "payment.reference_id",
        "payment.action.currency",
        "payment.action.action",
    ],
)
def test_payment_command_contains_invalid_field_value(
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

    1. Create a valid offchain PaymentCommand request object.
    2. Set a required field value to "invalid" by name defined by the test.
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `invalid_field_value` error code.
    """

    assert_payment_command_field_error(
        stub_config,
        stub_client,
        target_client,
        diem_client,
        currency,
        travel_rule_threshold,
        hrp,
        field_name,
        field_value="invalid",
        error_code="invalid_field_value",
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "_ObjectType",
        "payment",
        "payment.description",
        "payment.sender",
        "payment.sender.address",
        "payment.sender.status",
        "payment.sender.status.status",
        "payment.sender.metadata",
        "payment.receiver",
        "payment.receiver.address",
        "payment.receiver.status",
        "payment.receiver.status.status",
        "payment.receiver.metadata",
        "payment.reference_id",
        "payment.action",
        "payment.action.currency",
        "payment.action.action",
    ],
)
def test_payment_command_contains_invalid_field_value_type(
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

    1. Create a valid offchain PaymentCommand request object.
    2. Set a non-integer type field value to an integer number by name defined by the test.
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `invalid_field_value` error code.
    """

    assert_payment_command_field_error(
        stub_config,
        stub_client,
        target_client,
        diem_client,
        currency,
        travel_rule_threshold,
        hrp,
        field_name,
        field_value=123,
        error_code="invalid_field_value",
    )


def test_payment_command_contains_invalid_actor_metadata_item_type(
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

    1. Create a valid offchain PaymentCommand request object.
    2. Set sender actor metadata to a list of integer numbers.
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `invalid_field_value` error code.
    """

    assert_payment_command_field_error(
        stub_config,
        stub_client,
        target_client,
        diem_client,
        currency,
        travel_rule_threshold,
        hrp,
        "payment.sender.metadata",
        field_value=[123],
        error_code="invalid_field_value",
    )


def assert_payment_command_field_error(
    stub_config: AppConfig,
    stub_client: RestClient,
    target_client: RestClient,
    diem_client: jsonrpc.Client,
    currency: str,
    travel_rule_threshold: int,
    hrp: str,
    field_name: str,
    field_value: Union[None, str, int, List[int]],
    error_code: str,
) -> None:
    receiver_address = target_client.create_account().generate_account_identifier()
    sender_address = stub_client.create_account().generate_account_identifier()
    request = payment_command_request_sample(
        sender_address=sender_address,
        sender_kyc_data=target_client.new_kyc_data(sample="minimum"),
        receiver_address=receiver_address,
        currency=currency,
        amount=travel_rule_threshold,
    )
    full_field_name = "command." + field_name
    set_field(request, full_field_name, field_value)

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
    assert_response_error(resp, error_code, "command_error", field=full_field_name)
