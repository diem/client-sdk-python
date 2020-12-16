# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem.offchain import (
    state,
    replace_payment_actor,
    Action,
    individual_kyc_data,
    Status,
)
from diem.offchain.payment_state import (
    follow_up_action,
    Actor,
    MACHINE as machine,
    S_INIT,
    R_SEND,
    R_ABORT,
)
import dataclasses, pytest


def test_initial_state(factory):
    payment = factory.new_payment_object()

    initial_state = machine.match_state(payment)
    assert initial_state
    assert machine.is_initial(initial_state)
    assert S_INIT == initial_state


def test_match_state_validation(factory):
    payment = factory.new_payment_object()
    invalid_payment = dataclasses.replace(
        payment,
        receiver=replace_payment_actor(payment.receiver, status=Status.ready_for_settlement),
    )
    with pytest.raises(state.ConditionValidationError):
        machine.match_state(invalid_payment)


def test_match_receiver_ready_payment_state(factory):
    payment = factory.new_payment_object()
    receiver_ready_payment = dataclasses.replace(
        payment,
        receiver=replace_payment_actor(
            payment.receiver,
            status=Status.ready_for_settlement,
            kyc_data=individual_kyc_data(given_name="Rose"),
        ),
        recipient_signature="signature",
    )

    receiver_ready = machine.match_state(receiver_ready_payment)
    assert receiver_ready == R_SEND

    initial_state = machine.match_state(payment)
    assert machine.is_valid_transition(initial_state, receiver_ready, receiver_ready_payment)


def test_follow_up_action():
    assert follow_up_action(Actor.RECEIVER, S_INIT) == Action.EVALUATE_KYC_DATA
    assert follow_up_action(Actor.SENDER, R_SEND) == Action.EVALUATE_KYC_DATA
    assert follow_up_action(Actor.RECEIVER, R_SEND) is None
    assert follow_up_action(Actor.SENDER, R_ABORT) is None
    assert follow_up_action(Actor.RECEIVER, R_ABORT) is None
