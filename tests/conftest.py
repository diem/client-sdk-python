# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import time

from diem import testnet, offchain, identifier, LocalAccount
import pytest


@pytest.fixture
def factory():
    return Factory()


class Factory:
    def hrp(self) -> str:
        return identifier.TDM

    def create_offchain_client(self, account, client):
        return offchain.Client(account.account_address, client, self.hrp())

    def new_payment_object(self, sender=LocalAccount.generate(), receiver=LocalAccount.generate()):
        amount = 1_000_000_000_000
        currency = testnet.TEST_CURRENCY_CODE
        sender_account_id = identifier.encode_account(sender.account_address, identifier.gen_subaddress(), self.hrp())
        sender_kyc_data = offchain.individual_kyc_data(
            given_name="Jack",
            surname="G",
            address=offchain.AddressObject(city="San Francisco"),
        )

        receiver_account_id = identifier.encode_account(
            receiver.account_address,
            identifier.gen_subaddress(),
            self.hrp(),
        )

        return offchain.new_payment_object(
            sender_account_id,
            sender_kyc_data,
            receiver_account_id,
            amount,
            currency,
        )

    def new_sender_payment_command(self):
        payment = self.new_payment_object()
        return offchain.PaymentCommand(my_actor_address=payment.sender.address, payment=payment, inbound=False)

    def new_funds_pull_pre_approval_object(self, biller=LocalAccount.generate(), receiver=LocalAccount.generate()):
        address = identifier.encode_account(
            receiver.account_address,
            identifier.gen_subaddress(),
            self.hrp(),
        )

        biller_address = identifier.encode_account(
            biller.account_address,
            identifier.gen_subaddress(),
            self.hrp(),
        )

        return offchain.new_funds_pull_pre_approval_object(
            address=address,
            biller_address=biller_address,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=int(time.time()) + 30,
            status="pending",
            max_cumulative_unit="week",
            max_cumulative_unit_value=1,
            max_cumulative_amount=1_000_000_000_000,
            max_cumulative_amount_currency=testnet.TEST_CURRENCY_CODE,
            max_transaction_amount=1_000_000,
            max_transaction_amount_currency=testnet.TEST_CURRENCY_CODE,
            description="test",
        )

    def new_funds_pull_pre_approval_command(self):
        funds_pull_pre_approval = self.new_funds_pull_pre_approval_object()
        return offchain.FundsPullPreApprovalCommand(funds_pull_pre_approval=funds_pull_pre_approval)
