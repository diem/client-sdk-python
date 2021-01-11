# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import time
import uuid

from diem import testnet, offchain, identifier, LocalAccount
import pytest

from diem.offchain import (
    FundPullPreApprovalObject,
    FundPullPreApprovalScopeObject,
    ScopedCumulativeAmountObject,
    CurrencyObject,
    FundPullPreApprovalStatus,
)


@pytest.fixture(
    scope="module", params=[offchain.CommandType.PaymentCommand, offchain.CommandType.FundPullPreApprovalCommand]
)
def command_type(request):
    return request.param


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

        return FundPullPreApprovalObject(
            funds_pull_pre_approval_id=str(uuid.uuid4()),
            address=address,
            biller_address=biller_address,
            scope=FundPullPreApprovalScopeObject(
                type="consent",
                expiration_timestamp=int(time.time()) + 30,
                max_cumulative_amount=ScopedCumulativeAmountObject(
                    unit="week",
                    value=1,
                    max_amount=CurrencyObject(amount=1_000_000_000_000, currency=testnet.TEST_CURRENCY_CODE),
                ),
                max_transaction_amount=CurrencyObject(amount=1_000_000, currency=testnet.TEST_CURRENCY_CODE),
            ),
            status=FundPullPreApprovalStatus.valid,
            description="test",
        )

    def new_funds_pull_pre_approval_command(self):
        funds_pull_pre_approval = self.new_funds_pull_pre_approval_object()
        return offchain.FundsPullPreApprovalCommand(
            my_actor_address=identifier.encode_account(
                LocalAccount.generate().account_address,
                identifier.gen_subaddress(),
                self.hrp(),
            ),
            funds_pull_pre_approval=funds_pull_pre_approval,
        )

    def new_command(self, command_type, sender, receiver):
        if command_type == offchain.CommandType.PaymentCommand:
            payment = self.new_payment_object(sender, receiver)
            return offchain.PaymentCommand(payment=payment, my_actor_address=payment.sender.address, inbound=False)
        if command_type == offchain.CommandType.FundPullPreApprovalCommand:
            funds_pull_pre_approval = self.new_funds_pull_pre_approval_object(sender, receiver)
            return offchain.FundsPullPreApprovalCommand(
                my_actor_address=funds_pull_pre_approval.biller_address,
                funds_pull_pre_approval=funds_pull_pre_approval,
            )
