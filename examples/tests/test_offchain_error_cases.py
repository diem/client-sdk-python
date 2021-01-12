# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.offchain import (
    Status,
    Action,
    jws,
    http_header,
    CommandResponseObject,
    CommandResponseError,
    PaymentActionObject,
)
from diem import LocalAccount, identifier, testnet
from ..vasp.wallet import ActionResult
import dataclasses, requests, json, copy, pytest, uuid


AMOUNT = 1_000_000_000


def test_send_command_failed_by_invalid_jws_signature_and_retry_by_bg_job(monkeypatch, sender_app, receiver_app):
    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)

    with monkeypatch.context() as m:
        m.setattr(sender_app, "compliance_key", LocalAccount.generate().compliance_key)
        sender_app.pay("foo", intent_id)

        assert len(sender_app.saved_commands) == 1
        assert len(receiver_app.saved_commands) == 0

        with pytest.raises(CommandResponseError) as err:
            sender_app.run_once_background_job()

        assert_response_command_error(err.value.resp, "invalid_jws_signature")

        assert len(sender_app.saved_commands) == 1
        assert len(receiver_app.saved_commands) == 0

    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    assert len(sender_app.saved_commands) == 1
    assert len(receiver_app.saved_commands) == 1

    # receiver_app continues the flow after error is recovered
    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )


def test_send_command_failed_by_server_internal_error_and_retry_by_bg_job(monkeypatch, sender_app, receiver_app):
    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)

    with monkeypatch.context() as m:
        # receiver side save request failed, which causes 500 error to sender client
        m.setattr(
            receiver_app,
            "save_command",
            raise_error(Exception("simulate receiver app internal error")),
        )
        reference_id = sender_app.pay("foo", intent_id)
        with pytest.raises(Exception):
            sender_app.run_once_background_job()

        assert len(sender_app.saved_commands) == 1
        assert len(receiver_app.saved_commands) == 0

    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    assert len(sender_app.saved_commands) == 1
    assert len(receiver_app.saved_commands) == 1

    # receiver continues the flow after error is recovered
    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    with monkeypatch.context() as m:
        # receiver side save request failed, which causes 500 error to sender client
        m.setattr(
            receiver_app,
            "save_command",
            raise_error(Exception("simulate server internal error")),
        )

        # action success but send request should fail
        assert sender_app.run_once_background_job() == (
            Action.EVALUATE_KYC_DATA,
            ActionResult.PASS,
        )
        with pytest.raises(Exception):
            sender_app.run_once_background_job()

        assert sender_status(sender_app, reference_id) == Status.ready_for_settlement
        assert sender_status(receiver_app, reference_id) == Status.needs_kyc_data

        # retry failed again
        with pytest.raises(Exception):
            sender_app.run_once_background_job()

        assert sender_status(sender_app, reference_id) == Status.ready_for_settlement
        assert sender_status(receiver_app, reference_id) == Status.needs_kyc_data

    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_status(sender_app, reference_id) == Status.ready_for_settlement
    assert sender_status(receiver_app, reference_id) == Status.ready_for_settlement


def test_invalid_command_request_json(sender_app, receiver_app):
    resp = send_request("invalid_request_json", sender_app, receiver_app, "failure")

    assert resp.cid is None
    assert_response_command_error(resp, "invalid_object")


def test_invalid_json(sender_app, receiver_app):
    resp = send_request_json("invalid_json", sender_app, receiver_app, "failure")

    assert resp.cid is None
    assert_response_command_error(resp, "invalid_json")


def test_missing_required_fields(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)
    assert send_request(request, sender_app, receiver_app, "success")

    for field in find_all_fields(request):
        # ignore national_id which is optional, the id_value in national_id is required
        if field in ["command.payment.sender.kyc_data.national_id"]:
            continue
        new_req = copy.deepcopy(request)
        set_field(new_req, field, None)
        resp = send_request(new_req, sender_app, receiver_app, "failure")
        assert_response_command_error(resp, "missing_field", field)


def test_unknown_fields(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)

    for field in find_all_fields(request):
        new_req = copy.deepcopy(request)
        unknown_field = field + "-unknown"
        set_field(new_req, unknown_field, "any")
        resp = send_request(new_req, sender_app, receiver_app, "failure")
        assert_response_command_error(resp, "unknown_field", unknown_field)


def test_invalid_field_value(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)

    fields = [
        "_ObjectType",
        "command_type",
        "command._ObjectType",
        "command.payment.action.action",
        "command.payment.receiver.status.status",
        "command.payment.receiver.address",
        "command.payment.sender.address",
        "command.payment.sender.status.status",
        "command.payment.sender.kyc_data.type",
        "command.payment.sender.kyc_data.payload_version",
    ]
    for field in fields:
        new_req = copy.deepcopy(request)
        set_field(new_req, field, "invalid-value")
        resp = send_request(new_req, sender_app, receiver_app, "failure")
        assert_response_command_error(resp, "invalid_field_value", field)


def test_invalid_field_value_type(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)

    fields = [
        "command.payment.sender.status",  # status is object, status.status is status enum string
        "command.payment.sender.metadata",
    ]
    for field in fields:
        new_req = copy.deepcopy(request)
        set_field(new_req, field, "invalid-value-type")
        resp = send_request(new_req, sender_app, receiver_app, "failure")
        assert_response_command_error(resp, "invalid_field_value", field)


def test_invalid_actor_metadata_item_type(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)

    field = "command.payment.sender.metadata"
    set_field(request, field, ["1", 2])
    resp = send_request(request, sender_app, receiver_app, "failure")
    assert_response_command_error(resp, "invalid_field_value", field)


def test_written_once_payment_actor_kyc_data(sender_app, receiver_app):
    assert_invalid_overwrite_error(
        sender_app,
        receiver_app,
        "payment.sender.kyc_data",
        lambda cmd: replace_command_sender(cmd, kyc_data=sender_app.users["user-x"].kyc_data()),
    )


def test_written_once_payment_actor_additional_kyc_data(sender_app, receiver_app):
    assert_invalid_overwrite_error(
        sender_app,
        receiver_app,
        "payment.sender.additional_kyc_data",
        lambda cmd: replace_command_sender(cmd, additional_kyc_data="random stuff"),
    )


def test_written_once_payment_actor_address(sender_app, receiver_app):
    new_sender_address = sender_app.gen_user_account_id("user-x")

    def update_cmd(cmd):
        cmd = replace_command_sender(cmd, address=new_sender_address)
        return dataclasses.replace(cmd, my_actor_address=new_sender_address)

    assert_invalid_overwrite_error(sender_app, receiver_app, "payment.sender.address", update_cmd)


def test_written_once_payment_action(sender_app, receiver_app):
    assert_invalid_overwrite_error(
        sender_app,
        receiver_app,
        "payment.action",
        lambda cmd: replace_command_payment(cmd, action=PaymentActionObject(amount=AMOUNT, currency="XDX")),
    )


def test_written_once_payment_recipient_signature(sender_app, receiver_app):
    assert_invalid_overwrite_error(
        sender_app,
        receiver_app,
        "payment.recipient_signature",
        lambda cmd: replace_command_payment(cmd, recipient_signature="sig"),
    )


def test_written_once_payment_description(sender_app, receiver_app):
    assert_invalid_overwrite_error(
        sender_app,
        receiver_app,
        "payment.description",
        lambda cmd: replace_command_payment(cmd, description="want to change desc"),
    )


def test_written_once_payment_original_payment_reference_id(sender_app, receiver_app):
    assert_invalid_overwrite_error(
        sender_app,
        receiver_app,
        "payment.original_payment_reference_id",
        lambda cmd: replace_command_payment(cmd, original_payment_reference_id="4185027f-0574-6f55-2668-3a38fdb5de98"),
        original_payment_reference_id="6185027f-0574-6f55-2668-3a38fdb5de98",
    )


def test_written_once_payment_original_payment_reference_id_initial_only(sender_app, receiver_app):
    assert_invalid_overwrite_error(
        sender_app,
        receiver_app,
        "payment.original_payment_reference_id",
        lambda cmd: replace_command_payment(cmd, original_payment_reference_id="4185027f-0574-6f55-2668-3a38fdb5de98"),
    )


def test_update_opponent_actor_field_error(sender_app, receiver_app):
    assert_invalid_overwrite_error(
        sender_app,
        receiver_app,
        "payment.receiver",
        lambda cmd: replace_actor(cmd, "receiver", cmd.payment.receiver, additional_kyc_data="random stuff"),
    )


def test_resource_is_locked_error(sender_app, receiver_app):
    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    ref_id = sender_app.pay("foo", intent_id)
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    sender_app.lock(ref_id).acquire()
    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    with pytest.raises(CommandResponseError) as err:
        receiver_app.run_once_background_job()

    assert_response_command_error(err.value.resp, "conflict")


def test_travel_rule_limit_validation(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app, 10)

    resp = send_request(request, sender_app, receiver_app, "failure")
    assert_response_command_error(resp, "no_kyc_needed", "command.payment.action.amount")


def test_invalid_currency_code(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app, currency="XXX")

    resp = send_request(request, sender_app, receiver_app, "failure")
    assert_response_command_error(resp, "invalid_field_value", "command.payment.action.currency")


def test_cid_uuid(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)
    request["cid"] = "invalid uuid"
    resp = send_request(request, sender_app, receiver_app, "failure")
    assert_response_command_error(resp, "invalid_field_value", "cid")


def test_reference_id_uuid(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)
    request["command"]["payment"]["reference_id"] = "invalid uuid"
    resp = send_request(request, sender_app, receiver_app, "failure")
    assert_response_command_error(resp, "invalid_field_value", "command.payment.reference_id")


def test_unknown_actor_address_could_not_find_request_receiver_account_id(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)
    request["command"]["payment"]["receiver"]["address"] = sender_app.offchain_client.my_compliance_key_account_id
    resp = send_request(request, sender_app, receiver_app, "failure")
    assert_response_command_error(resp, "unknown_actor_address")


def test_x_request_sender_address_must_one_of_actor_addresses(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)
    resp = send_request(
        request,
        sender_app,
        receiver_app,
        "failure",
        sender_address=sender_app.offchain_client.my_compliance_key_account_id,
    )
    assert_response_command_error(resp, "invalid_x_request_sender_address")


def test_http_header_x_request_sender_address_missing(sender_app, receiver_app):
    request = minimum_required_fields_request_sample(sender_app, receiver_app)
    resp = send_request_json_with_headers(
        json.dumps(request), sender_app, receiver_app, "failure", {http_header.X_REQUEST_ID: str(uuid.uuid4())}
    )
    assert_response_protocol_error(resp, "missing_http_header")


def test_could_not_find_onchain_account_by_x_request_sender_address(sender_app, receiver_app):
    account = LocalAccount.generate()
    account_id = identifier.encode_account(account.account_address, None, sender_app.hrp)
    request = minimum_required_fields_request_sample(sender_app, receiver_app)
    request["command"]["payment"]["sender"]["address"] = account_id
    resp = send_request(request, sender_app, receiver_app, "failure", sender_address=account_id)
    assert_response_protocol_error(resp, "invalid_x_request_sender_address")


def test_could_not_find_compliance_key_of_x_request_sender_address(sender_app, receiver_app):
    account = testnet.gen_account(testnet.create_client())
    account_id = identifier.encode_account(account.account_address, None, sender_app.hrp)
    request = minimum_required_fields_request_sample(sender_app, receiver_app)
    request["command"]["payment"]["sender"]["address"] = account_id
    resp = send_request(request, sender_app, receiver_app, "failure", sender_address=account_id)
    assert_response_protocol_error(resp, "invalid_x_request_sender_address")


def test_invalid_recipient_signature(sender_app, receiver_app):
    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    ref_id = sender_app.pay("foo", intent_id)
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    cmd = receiver_app.saved_commands.get(ref_id)
    invalid_sig_cmd = replace_command_payment(cmd, recipient_signature=b"invalid-sig".hex())
    with pytest.raises(CommandResponseError) as err:
        assert receiver_app._send_request(invalid_sig_cmd)

    assert_response_command_error(err.value.resp, "invalid_recipient_signature", "command.payment.recipient_signature")


def test_receiver_actor_is_ready_for_settlement_but_recipient_signature_is_none(sender_app, receiver_app):
    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    ref_id = sender_app.pay("foo", intent_id)
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    cmd = receiver_app.saved_commands.get(ref_id)
    missing_sig_cmd = replace_command_payment(cmd, recipient_signature=None)
    with pytest.raises(CommandResponseError) as err:
        assert receiver_app._send_request(missing_sig_cmd)

    assert_response_command_error(err.value.resp, "missing_field", "command.payment.recipient_signature")


def test_invalid_recipient_signature_hex(sender_app, receiver_app):
    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    ref_id = sender_app.pay("foo", intent_id)
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    cmd = receiver_app.saved_commands.get(ref_id)
    invalid_sig_cmd = replace_command_payment(cmd, recipient_signature="invalid-sig-hex")
    with pytest.raises(CommandResponseError) as err:
        assert receiver_app._send_request(invalid_sig_cmd)

    assert_response_command_error(err.value.resp, "invalid_recipient_signature", "command.payment.recipient_signature")


def replace_actor(cmd, name, actor, **changes):
    new_actor = dataclasses.replace(actor, **changes)
    return replace_command_payment(cmd, **{name: new_actor})


def replace_command_sender(cmd, **changes):
    return replace_actor(cmd, "sender", cmd.payment.sender, **changes)


def replace_command_payment(cmd, **changes):
    new_payment = dataclasses.replace(cmd.payment, **changes)
    return dataclasses.replace(cmd, payment=new_payment)


def assert_invalid_overwrite_error(sender_app, receiver_app, field, update_cmd, original_payment_reference_id=None):
    # setup soft match for sender provide additional_kyc_data
    receiver_app.evaluate_kyc_data_result = {"foo": ActionResult.SOFT_MATCH}
    receiver_app.manual_review_result = {"foo": ActionResult.PASS}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    ref_id = sender_app.pay(
        "foo", intent_id, original_payment_reference_id=original_payment_reference_id, desc="this is a good deal"
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.SOFT_MATCH,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.CLEAR_SOFT_MATCH,
        ActionResult.SENT_ADDITIONAL_KYC_DATA,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.REVIEW_KYC_DATA,
        ActionResult.PASS,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    # sender provided kyc_data and additional_kyc_data
    # receiver provided signature and kyc_data

    assert len(sender_app.saved_commands) == 1

    cmd = sender_app.saved_commands.get(ref_id)
    sender_app.saved_commands[ref_id] = update_cmd(cmd)

    assert sender_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    with pytest.raises(CommandResponseError) as err:
        sender_app.run_once_background_job()

    assert_response_command_error(err.value.resp, "invalid_overwrite", field)


def assert_response_command_error(resp, code, field=None):
    assert_response_error(resp, code, "command_error", field)


def assert_response_protocol_error(resp, code, field=None):
    assert_response_error(resp, code, "protocol_error", field)


def assert_response_error(resp, code, err_type, field=None):
    assert resp.error, resp
    assert resp.error.type == err_type, resp
    assert resp.error.code == code, resp
    assert resp.error.field == field, resp


def set_field(dic, field, value):
    path = field.split(".")
    for f in path[0 : len(path) - 1]:
        if f not in dic:
            dic[f] = {}
        dic = dic[f]

    dic[path[len(path) - 1]] = value


def find_all_fields(dic):
    ret = []
    for key in dic:
        ret.append(key)
        if isinstance(dic[key], dict):
            sub_fields = find_all_fields(dic[key])
            for sf in sub_fields:
                ret.append(".".join([key, sf]))
    return ret


def send_request(request, sender_app, receiver_app, expected_resp_status, sender_address=None) -> CommandResponseObject:
    return send_request_json(json.dumps(request), sender_app, receiver_app, expected_resp_status, sender_address)


def send_request_json(
    request_json, sender_app, receiver_app, expected_resp_status, sender_address=None
) -> CommandResponseObject:
    if sender_address is None:
        subaddresses = sender_app.users["foo"].subaddresses
        subaddress = subaddresses[len(subaddresses) - 1] if len(subaddresses) > 0 else None
        account_address = sender_app._available_child_vasp().account_address
        sender_address = identifier.encode_account(account_address, subaddress, sender_app.hrp)
    return send_request_json_with_headers(
        request_json,
        sender_app,
        receiver_app,
        expected_resp_status,
        {
            http_header.X_REQUEST_ID: str(uuid.uuid4()),
            http_header.X_REQUEST_SENDER_ADDRESS: sender_address,
        },
    )


def send_request_json_with_headers(
    request_json, sender_app, receiver_app, expected_resp_status, headers
) -> CommandResponseObject:
    session = requests.Session()
    resp = session.post(
        f"http://localhost:{receiver_app.offchain_service_port}/v2/command",
        data=jws.serialize_string(request_json, sender_app.compliance_key.sign),
        headers=headers,
    )

    cmd_resp_obj = jws.deserialize(
        resp.content,
        CommandResponseObject,
        receiver_app.compliance_key.public_key().verify,
    )
    assert cmd_resp_obj.status == expected_resp_status
    if expected_resp_status == "success":
        assert resp.status_code == 200
    else:
        assert resp.status_code == 400

    return cmd_resp_obj


def sender_status(wallet, ref_id):
    command = wallet.saved_commands[ref_id]
    return command.payment.sender.status.status


def raise_error(e: Exception):
    def fn(*args, **wargs):
        raise e

    return fn


def minimum_required_fields_request_sample(sender_app, receiver_app, amount=AMOUNT, currency="XUS"):
    return {
        "_ObjectType": "CommandRequestObject",
        "cid": "3185027f-0574-6f55-2668-3a38fdb5de98",
        "command_type": "PaymentCommand",
        "command": {
            "_ObjectType": "PaymentCommand",
            "payment": {
                "reference_id": "4185027f-0574-6f55-2668-3a38fdb5de98",
                "sender": {
                    "address": sender_app.gen_user_account_id("foo"),
                    "status": {"status": "needs_kyc_data"},
                    "kyc_data": {
                        "type": "individual",
                        "payload_version": 1,
                        "national_id": {"id_value": "332-323-4344"},
                    },
                },
                "receiver": {
                    "address": receiver_app.gen_user_account_id("bar"),
                    "status": {"status": "none"},
                },
                "action": {
                    "amount": amount,
                    "currency": currency,
                    "action": "charge",
                    "timestamp": 1604902048,
                },
            },
        },
    }
