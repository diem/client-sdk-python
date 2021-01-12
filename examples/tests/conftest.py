# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from ..vasp import WalletApp
from diem import testnet, jsonrpc
import pytest, typing


def launch_wallet_app(name: str, client: jsonrpc.Client) -> WalletApp:
    app = WalletApp.generate(f"{name}'s wallet app", client)
    app.start_server()
    return app


@pytest.fixture(scope="module")
def wallet_apps() -> typing.List[WalletApp]:
    client = testnet.create_client()
    return {name: launch_wallet_app(name, client) for name in ["sender", "receiver"]}


@pytest.fixture
def sender_app(wallet_apps):
    yield from with_users(wallet_apps["sender"], ["foo", "user-x", "hello"])


@pytest.fixture
def receiver_app(wallet_apps):
    yield from with_users(wallet_apps["receiver"], ["bar", "user-y", "world"])


def with_users(app, users):
    for user in users:
        app.add_user(user)
    yield app
    app.clear_data()


@pytest.fixture()
def assert_final_status(sender_app, receiver_app):
    sender_vasp_balance = sender_app.vasp_balance()
    receiver_vasp_balance = receiver_app.vasp_balance()

    def assert_fn(
        final_status: typing.Dict[str, str],
        balance_change: typing.Optional[int] = 0,
    ) -> None:

        sender_cmd = sender_app.saved_commands
        receiver_cmd = receiver_app.saved_commands
        assert len(sender_cmd) == 1
        assert len(receiver_cmd) == 1

        ref_id = list(sender_cmd.keys())[0]
        sender_record = sender_cmd[ref_id]
        assert sender_record.cid == receiver_cmd[ref_id].cid
        assert sender_record.payment == receiver_cmd[ref_id].payment

        assert sender_record.payment.sender.status.status == final_status["sender"]
        assert sender_record.payment.receiver.status.status == final_status["receiver"]

        assert sender_app.vasp_balance() == sender_vasp_balance - balance_change
        assert receiver_app.vasp_balance() == receiver_vasp_balance + balance_change

        # nothing left
        assert sender_app.run_once_background_job() is None
        assert receiver_app.run_once_background_job() is None

    return assert_fn
