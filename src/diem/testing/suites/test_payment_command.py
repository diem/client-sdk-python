# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import jsonrpc
from diem.testing.miniwallet import RestClient, AppConfig
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
def test_payment_command_missing_required_field(
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
    2. Remove a required field by name defined by the test
    3. Send the request to the target wallet application offchain API endpoint.
    4. Expect response status code is 400
    5. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `missing_field` error code.
    """

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
    set_field(request, full_field_name, None)

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
    assert_response_error(resp, "missing_field", "command_error", field=full_field_name)
