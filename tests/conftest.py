# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import testnet, offchain, identifier, chain_ids, LocalAccount
from os import getenv, system
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_testnet():
    if getenv("dt"):
        system("make docker")
        print("swap testnet default values to local testnet launched by docker-compose")
        testnet.JSON_RPC_URL = "http://localhost:8080/v1"
        testnet.FAUCET_URL = "http://localhost:8000/mint"
        testnet.CHAIN_ID = chain_ids.TESTING
        yield 1
        if getenv("dts"):
            system("make docker-stop")
    else:
        yield 0


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
        sender_account_id = sender.account_identifier(identifier.gen_subaddress())
        sender_kyc_data = offchain.individual_kyc_data(
            given_name="Jack",
            surname="G",
            address=offchain.AddressObject(city="San Francisco"),
        )

        receiver_account_id = receiver.account_identifier(identifier.gen_subaddress())

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
