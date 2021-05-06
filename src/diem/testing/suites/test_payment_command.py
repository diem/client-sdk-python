# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import replace
from diem import jsonrpc, offchain, identifier
from diem.testing.miniwallet import RestClient, AppConfig, App, Transaction, PaymentCommand
from typing import Union, List
from .conftest import (
    set_field,
    assert_response_error,
    payment_command_request_sample,
    send_request_json,
)
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
    4. Expect http response status code is 400
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
    4. Expect http response status code is 400
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
    4. Expect http response status code is 400
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
    4. Expect http response status code is 400
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
    4. Expect http response status code is 400
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


def test_replay_the_same_payment_command(
    currency: str,
    travel_rule_threshold: int,
    stub_wallet_app: App,
    stub_client: RestClient,
    target_client: RestClient,
) -> None:
    """
    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Disable stub wallet application background tasks.
    3. Send a payment that requires off-chain PaymentCommand to the receiver account identifier.
    4. Send initial payment command to receiver wallet offchain API endpoint.
    5. Re-send the offchain PaymentCommand.
    6. Expect no error raised.
    7. Enable stub wallet application background tasks.
    """

    sender_account = stub_client.create_account(
        balances={currency: travel_rule_threshold},
        kyc_data=target_client.get_kyc_sample().minimum,
        disable_background_tasks=True,
    )
    receiver_account = target_client.create_account(kyc_data=stub_client.get_kyc_sample().minimum)
    try:
        payee = receiver_account.generate_account_identifier()

        payment = sender_account.send_payment(currency=currency, amount=travel_rule_threshold, payee=payee)
        txn = stub_wallet_app.store.find(Transaction, id=payment.id)
        # send initial payment command
        cmd = stub_wallet_app.send_initial_payment_command(txn)
        stub_wallet_app.send_offchain_command_without_retries(cmd)
        stub_wallet_app.send_offchain_command_without_retries(cmd)
    finally:
        receiver_account.log_events()
        sender_account.log_events()


def test_payment_command_sender_kyc_data_can_only_be_written_once(
    currency: str,
    travel_rule_threshold: int,
    stub_wallet_app: App,
    stub_client: RestClient,
    target_client: RestClient,
) -> None:
    """
    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Disable stub wallet application background tasks.
    3. Send a payment that requires off-chain PaymentCommand to the receiver account identifier.
    4. Send initial payment command to receiver wallet offchain API endpoint.
    5. Wait for receiver's wallet application to send payment command back with receiver ready for settlement.
    6. Update payment command sender KYC data.
    7. Send the updated payment command to receiver with sender ready for settlement.
    8. Expect http response status code is 400
    9. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `invalid_overwrite` error code.
    """

    sender_account = stub_client.create_account(
        balances={currency: travel_rule_threshold},
        kyc_data=target_client.get_kyc_sample().minimum,
        disable_background_tasks=True,
    )
    receiver_account = target_client.create_account(kyc_data=stub_client.get_kyc_sample().minimum)
    try:
        payee = receiver_account.generate_account_identifier()

        payment = sender_account.send_payment(currency=currency, amount=travel_rule_threshold, payee=payee)
        txn = stub_wallet_app.store.find(Transaction, id=payment.id)
        # send initial payment command
        initial_cmd = stub_wallet_app.send_initial_payment_command(txn)

        # wait for receiver to update payment command
        sender_account.wait_for_event("updated_payment_command")
        # find updated payment command
        updated_cmd = stub_wallet_app.store.find(PaymentCommand, reference_id=initial_cmd.reference_id())
        offchain_cmd = updated_cmd.to_offchain_command()

        # update sender KYC data
        assert offchain_cmd.payment.sender.kyc_data
        if offchain_cmd.payment.sender.kyc_data.dob == "01/01/1979":
            kyc_data = replace(offchain_cmd.payment.sender.kyc_data, dob="01/01/1979")
        else:
            kyc_data = replace(offchain_cmd.payment.sender.kyc_data, dob="01/02/1979")
        # create new payment command with correct status and changed kyc data
        new_cmd = offchain_cmd.new_command(status=offchain.Status.ready_for_settlement, kyc_data=kyc_data)

        with pytest.raises(offchain.CommandResponseError) as err:
            stub_wallet_app.send_offchain_command_without_retries(new_cmd)

        assert_response_error(err.value.resp, "invalid_overwrite", "command_error", field="payment.sender.kyc_data")
    finally:
        receiver_account.log_events()
        sender_account.log_events()


def test_payment_command_sender_address_can_only_be_written_once(
    currency: str,
    travel_rule_threshold: int,
    stub_wallet_app: App,
    hrp: str,
    stub_client: RestClient,
    target_client: RestClient,
) -> None:
    """
    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Disable stub wallet application background tasks.
    3. Send a payment that requires off-chain PaymentCommand to the receiver account identifier.
    4. Send initial payment command to receiver wallet offchain API endpoint.
    5. Wait for receiver's wallet application to send payment command back with receiver ready for settlement.
    6. Update payment command sender address.
    7. Send the updated payment command to receiver with sender ready for settlement.
    8. Expect http response status code is 400
    9. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `invalid_overwrite` error code.
    """

    sender_account = stub_client.create_account(
        balances={currency: travel_rule_threshold},
        kyc_data=target_client.get_kyc_sample().minimum,
        disable_background_tasks=True,
    )
    receiver_account = target_client.create_account(kyc_data=stub_client.get_kyc_sample().minimum)
    try:
        payee = receiver_account.generate_account_identifier()

        payment = sender_account.send_payment(currency=currency, amount=travel_rule_threshold, payee=payee)
        txn = stub_wallet_app.store.find(Transaction, id=payment.id)
        # send initial payment command
        initial_cmd = stub_wallet_app.send_initial_payment_command(txn)

        # wait for receiver to update payment command
        sender_account.wait_for_event("updated_payment_command")
        # find updated payment command
        updated_cmd = stub_wallet_app.store.find(PaymentCommand, reference_id=initial_cmd.reference_id())
        offchain_cmd = updated_cmd.to_offchain_command()

        # update sender address
        sender_account_address = offchain_cmd.sender_account_address(hrp)
        new_subaddress = stub_wallet_app._gen_subaddress(sender_account.id)
        new_sender_address = identifier.encode_account(sender_account_address, new_subaddress, hrp)
        new_sender = replace(offchain_cmd.payment.sender, address=new_sender_address)
        new_payment = replace(offchain_cmd.payment, sender=new_sender)
        new_offchain_cmd = replace(offchain_cmd, payment=new_payment, my_actor_address=new_sender_address)

        new_cmd = new_offchain_cmd.new_command(status=offchain.Status.ready_for_settlement)

        with pytest.raises(offchain.CommandResponseError) as err:
            stub_wallet_app.send_offchain_command_without_retries(new_cmd)

        assert_response_error(err.value.resp, "invalid_overwrite", "command_error", field="payment.sender.address")
    finally:
        receiver_account.log_events()
        sender_account.log_events()


@pytest.mark.parametrize(
    "field_name",
    [
        "currency",
        "amount",
        "timestamp",
    ],
)
def test_payment_command_action_can_only_be_written_once(
    currency: str,
    travel_rule_threshold: int,
    stub_wallet_app: App,
    hrp: str,
    stub_client: RestClient,
    target_client: RestClient,
    field_name: str,
) -> None:
    """
    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Disable stub wallet application background tasks.
    3. Send a payment that requires off-chain PaymentCommand to the receiver account identifier.
    4. Send initial payment command to receiver wallet offchain API endpoint.
    5. Wait for receiver's wallet application to send payment command back with receiver ready for settlement.
    6. Update payment command action.
    7. Send the updated payment command to receiver with sender ready for settlement.
    8. Expect http response status code is 400
    9. Expect response `CommandResponseObject` with failure status, `command_error` error type,
       and `invalid_overwrite` error code.
    """

    sender_account = stub_client.create_account(
        balances={currency: travel_rule_threshold},
        kyc_data=target_client.get_kyc_sample().minimum,
        disable_background_tasks=True,
    )
    receiver_account = target_client.create_account(kyc_data=stub_client.get_kyc_sample().minimum)
    try:
        payee = receiver_account.generate_account_identifier()

        payment = sender_account.send_payment(currency=currency, amount=travel_rule_threshold, payee=payee)
        txn = stub_wallet_app.store.find(Transaction, id=payment.id)
        # send initial payment command
        initial_cmd = stub_wallet_app.send_initial_payment_command(txn)

        # wait for receiver to update payment command
        sender_account.wait_for_event("updated_payment_command")
        # find updated payment command
        updated_cmd = stub_wallet_app.store.find(PaymentCommand, reference_id=initial_cmd.reference_id())
        offchain_cmd = updated_cmd.to_offchain_command()

        # update action field value
        if field_name == "currency":
            field_value = "XDX" if offchain_cmd.payment.action.currency == "XUS" else "XUS"
        elif field_name == "amount":
            field_value = offchain_cmd.payment.action.amount + 10_000
        elif field_name == "timestamp":
            field_value = offchain_cmd.payment.action.timestamp - 1
        new_action = replace(offchain_cmd.payment.action, **{field_name: field_value})
        new_payment = replace(offchain_cmd.payment, action=new_action)
        new_offchain_cmd = replace(offchain_cmd, payment=new_payment)

        new_cmd = new_offchain_cmd.new_command(status=offchain.Status.ready_for_settlement)

        with pytest.raises(offchain.CommandResponseError) as err:
            stub_wallet_app.send_offchain_command_without_retries(new_cmd)

        assert_response_error(err.value.resp, "invalid_overwrite", "command_error", field="payment.action")
    finally:
        receiver_account.log_events()
        sender_account.log_events()


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
        sender_kyc_data=target_client.get_kyc_sample().minimum,
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
