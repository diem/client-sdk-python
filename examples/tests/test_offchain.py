# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.offchain import Status, Action
from ..vasp.wallet import ActionResult


AMOUNT = 1_000_000_000
BOTH_READY = {
    "sender": Status.ready_for_settlement,
    "receiver": Status.ready_for_settlement,
}


def test_travel_rule_data_exchange_happy_path(sender_app, receiver_app, assert_final_status):
    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

    assert len(sender_app.saved_commands) == 1
    assert len(receiver_app.saved_commands) == 0

    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert len(receiver_app.saved_commands) == 1

    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    assert sender_app.run_once_background_job() is None
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    assert receiver_app.run_once_background_job() is None
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() is None
    assert sender_app.run_once_background_job() == (
        Action.SUBMIT_TXN,
        ActionResult.TXN_EXECUTED,
    )
    assert receiver_app.run_once_background_job() is None

    assert_final_status(BOTH_READY, AMOUNT)


def test_travel_rule_data_exchange_receiver_reject_sender_kyc_data(sender_app, receiver_app, assert_final_status):
    receiver_app.evaluate_kyc_data_result = {"foo": ActionResult.REJECT}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.REJECT,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    assert_final_status({"sender": Status.needs_kyc_data, "receiver": Status.abort})


def test_travel_rule_data_exchange_receiver_soft_match_reject(sender_app, receiver_app, assert_final_status):
    receiver_app.evaluate_kyc_data_result = {"foo": ActionResult.SOFT_MATCH}
    receiver_app.manual_review_result = {"foo": ActionResult.REJECT}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

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
        ActionResult.REJECT,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS

    assert_final_status({"sender": Status.needs_kyc_data, "receiver": Status.abort})


def test_travel_rule_data_exchange_receiver_soft_match_pass(sender_app, receiver_app, assert_final_status):
    receiver_app.evaluate_kyc_data_result = {"foo": ActionResult.SOFT_MATCH}
    receiver_app.manual_review_result = {"foo": ActionResult.PASS}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

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
    assert sender_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() is None

    assert sender_app.run_once_background_job() == (
        Action.SUBMIT_TXN,
        ActionResult.TXN_EXECUTED,
    )
    assert receiver_app.run_once_background_job() is None

    assert_final_status(BOTH_READY, AMOUNT)


def test_travel_rule_data_exchange_sender_rejects_receiver_kyc_data(sender_app, receiver_app, assert_final_status):
    sender_app.evaluate_kyc_data_result = {"bar": ActionResult.REJECT}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.REJECT,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() is None

    assert_final_status({"sender": Status.abort, "receiver": Status.ready_for_settlement})


def test_travel_rule_data_exchange_sender_soft_match_reject(sender_app, receiver_app, assert_final_status):
    sender_app.evaluate_kyc_data_result = {"bar": ActionResult.SOFT_MATCH}
    sender_app.manual_review_result = {"bar": ActionResult.REJECT}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.SOFT_MATCH,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.CLEAR_SOFT_MATCH,
        ActionResult.SENT_ADDITIONAL_KYC_DATA,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.REVIEW_KYC_DATA,
        ActionResult.REJECT,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() is None

    assert_final_status({"sender": Status.abort, "receiver": Status.ready_for_settlement})


def test_travel_rule_data_exchange_sender_soft_match_pass(sender_app, receiver_app, assert_final_status):
    sender_app.evaluate_kyc_data_result = {"bar": ActionResult.SOFT_MATCH}
    sender_app.manual_review_result = {"bar": ActionResult.PASS}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.PASS,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.SOFT_MATCH,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.CLEAR_SOFT_MATCH,
        ActionResult.SENT_ADDITIONAL_KYC_DATA,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.REVIEW_KYC_DATA,
        ActionResult.PASS,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() is None
    assert sender_app.run_once_background_job() == (
        Action.SUBMIT_TXN,
        ActionResult.TXN_EXECUTED,
    )
    assert receiver_app.run_once_background_job() is None

    assert_final_status(BOTH_READY, AMOUNT)


def test_travel_rule_data_exchange_receiver_soft_match_pass_sender_soft_match_reject(
    sender_app, receiver_app, assert_final_status
):
    receiver_app.evaluate_kyc_data_result = {"foo": ActionResult.SOFT_MATCH}
    receiver_app.manual_review_result = {"foo": ActionResult.PASS}
    sender_app.evaluate_kyc_data_result = {"bar": ActionResult.SOFT_MATCH}
    sender_app.manual_review_result = {"bar": ActionResult.REJECT}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

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

    assert sender_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.SOFT_MATCH,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.CLEAR_SOFT_MATCH,
        ActionResult.SENT_ADDITIONAL_KYC_DATA,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.REVIEW_KYC_DATA,
        ActionResult.REJECT,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() is None

    assert_final_status({"sender": Status.abort, "receiver": Status.ready_for_settlement})


def test_travel_rule_data_exchange_receiver_soft_match_pass_sender_soft_match_pass(
    sender_app, receiver_app, assert_final_status
):
    receiver_app.evaluate_kyc_data_result = {"foo": ActionResult.SOFT_MATCH}
    receiver_app.manual_review_result = {"foo": ActionResult.PASS}
    sender_app.evaluate_kyc_data_result = {"bar": ActionResult.SOFT_MATCH}
    sender_app.manual_review_result = {"bar": ActionResult.PASS}

    intent_id = receiver_app.gen_intent_id("bar", AMOUNT)
    sender_app.pay("foo", intent_id)

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

    assert sender_app.run_once_background_job() == (
        Action.EVALUATE_KYC_DATA,
        ActionResult.SOFT_MATCH,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() == (
        Action.CLEAR_SOFT_MATCH,
        ActionResult.SENT_ADDITIONAL_KYC_DATA,
    )
    assert receiver_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert sender_app.run_once_background_job() == (
        Action.REVIEW_KYC_DATA,
        ActionResult.PASS,
    )
    assert sender_app.run_once_background_job() == ActionResult.SEND_REQUEST_SUCCESS
    assert receiver_app.run_once_background_job() is None

    assert sender_app.run_once_background_job() == (
        Action.SUBMIT_TXN,
        ActionResult.TXN_EXECUTED,
    )
    assert receiver_app.run_once_background_job() is None

    assert_final_status(BOTH_READY, AMOUNT)
