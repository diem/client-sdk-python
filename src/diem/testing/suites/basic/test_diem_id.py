# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import identifier
from diem.testing.miniwallet import RestClient
from diem.testing.suites.conftest import wait_for_balance
from typing import List


def test_receive_payment_with_diem_id(
    stub_client: RestClient,
    target_client: RestClient,
    target_account_diem_id_domains: List[str],
    currency: str,
) -> None:
    sender_starting_balance = 1_000_000
    sender_account = stub_client.create_account(balances={currency: sender_starting_balance})
    receiver_account = target_client.create_account()
    payee_diem_id = identifier.diem_id.create_diem_id(receiver_account.id, target_account_diem_id_domains[0])
    amount = 150_000
    sender_account.send_payment(currency, amount, payee_diem_id)
    wait_for_balance(sender_account, currency, sender_starting_balance - amount)
    wait_for_balance(receiver_account, currency, amount)


def test_send_payment_with_diem_id(
    stub_client: RestClient,
    target_client: RestClient,
    stub_account_diem_id_domains: List[str],
    currency: str,
) -> None:
    sender_starting_balance = 1_000_000
    sender_account = target_client.create_account(balances={currency: sender_starting_balance})
    receiver_account = stub_client.create_account()
    payee_diem_id = identifier.diem_id.create_diem_id(receiver_account.id, stub_account_diem_id_domains[0])
    amount = 230_000
    sender_account.send_payment(currency, amount, payee_diem_id)
    wait_for_balance(sender_account, currency, sender_starting_balance - amount)
    wait_for_balance(receiver_account, currency, amount)
