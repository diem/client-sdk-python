# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain, jsonrpc, stdlib, utils, txnmetadata, identifier
from diem.jsonrpc import AsyncClient
from diem.testing.miniwallet import RestClient, AccountResource, Transaction, AppConfig
from typing import Optional, List
from ..conftest import wait_for, wait_for_balance, wait_for_event, wait_for_payment_transaction_complete
import pytest, json


pytestmark = pytest.mark.asyncio  # pyre-ignore


async def test_receive_payment_with_travel_rule_metadata_and_valid_reference_id(
    stub_client: RestClient, target_client: RestClient, currency: str, travel_rule_threshold: int
) -> None:
    """
    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Send a payment meeting travel rule threshold to the account identifier.
    3. Wait for the transaction executed successfully.
    4. Assert receiver account received the fund.

    """
    amount = travel_rule_threshold
    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    sender_account = await stub_client.create_account(balances={currency: amount}, kyc_data=target_kyc.minimum)
    receiver_account = await target_client.create_account(kyc_data=stub_kyc.minimum)
    try:
        account_identifier = await receiver_account.generate_account_identifier()
        pay = await sender_account.send_payment(currency, travel_rule_threshold, payee=account_identifier)
        await wait_for_payment_transaction_complete(sender_account, pay.id)
        await wait_for_balance(receiver_account, currency, travel_rule_threshold)
    finally:
        await receiver_account.log_events()
        await sender_account.log_events()


@pytest.mark.parametrize("invalid_ref_id", [None, "", "ref_id_is_not_uuid", "6cd81d79-f041-4f28-867f-e4d54950833e"])
async def test_receive_payment_with_travel_rule_metadata_and_invalid_reference_id(
    stub_client: RestClient,
    target_client: RestClient,
    currency: str,
    hrp: str,
    stub_config: AppConfig,
    diem_client: AsyncClient,
    stub_wallet_pending_income_account: AccountResource,
    invalid_ref_id: Optional[str],
    travel_rule_threshold: int,
) -> None:
    """
    There is no way to create travel rule metadata with invalid reference id when the payment
    amount meets travel rule threshold, because the metadata signature is verified by transaction
    script.
    Also, if metadata signature is provided, transaction script will also verify it regardless
    whether the amount meets travel rule threshold, thus no need to test invalid metadata
    signature case.

    This test bypasses the transaction script validation by sending payment amount under the
    travel rule threshold without metadata signature, and receiver should handle it properly and refund.

    Test Plan:

    1. Generate a valid account identifier from receiver account as payee.
    2. Submit payment under travel rule threshold transaction from sender to receiver on-chain account.
    3. Wait for the transaction executed successfully.
    4. Assert the payment is refund eventually.

    Note: the refund payment will be received by pending income account of the MiniWallet Stub, because
    no account owns the original invalid payment transaction which is sent by test.

    """

    amount = travel_rule_threshold
    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    sender_account = await stub_client.create_account(balances={currency: amount}, kyc_data=target_kyc.minimum)
    receiver_account = await target_client.create_account(kyc_data=stub_kyc.minimum)
    try:
        receiver_account_identifier = await receiver_account.generate_account_identifier()
        receiver_account_address = identifier.decode_account_address(receiver_account_identifier, hrp)

        sender_account_identifier = await sender_account.generate_account_identifier()
        sender_address = identifier.decode_account_address(sender_account_identifier, hrp)
        metadata, _ = txnmetadata.travel_rule(invalid_ref_id, sender_address, amount)  # pyre-ignore
        original_payment_txn: jsonrpc.Transaction = await stub_config.account.submit_and_wait_for_txn(
            diem_client,
            stdlib.encode_peer_to_peer_with_metadata_script_function(
                currency=utils.currency_code(currency),
                amount=amount / 1000,
                payee=receiver_account_address,
                metadata=metadata,
                metadata_signature=b"",
            ),
        )

        await wait_for_event(
            stub_wallet_pending_income_account,
            "created_transaction",
            status=Transaction.Status.completed,
            refund_diem_txn_version=original_payment_txn.version,
        )
        assert await receiver_account.balance(currency) == 0
    finally:
        await receiver_account.log_events()
        await sender_account.log_events()


async def test_receive_payment_meets_travel_rule_threshold_both_kyc_data_evaluations_are_accepted(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with minimum valid kyc data with 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "READY"]
    5 . Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.minimum
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.minimum),
        payment_command_states=["S_INIT", "R_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_rejected_by_the_receiver(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient, hrp: str
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be rejected by the target wallet application in the stub wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_ABORT"]
    5 . Expect sender and receiver accounts' balances are not changed.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(balances={currency: travel_rule_threshold}, kyc_data=target_kyc.reject),
        receiver=await target_client.create_account(kyc_data=stub_kyc.minimum),
        payment_command_states=["S_INIT", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_receiver_kyc_data_is_rejected_by_the_sender(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be rejected by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.minimum
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.reject),
        payment_command_states=["S_INIT", "R_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched by the target wallet application and enough balance in the stub wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "READY"]
    4. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.soft_match
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.minimum),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_receiver_kyc_data_is_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"]
    5. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.minimum
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.soft_match),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_rejected_after_reviewing_additional_kyc_data(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then rejected by the target wallet application in the stub wallet application.
    2. Create receiver account with minimum valid kyc data and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.soft_reject
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.minimum),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_receiver_kyc_data_is_soft_match_then_rejected_after_reviewing_additional_kyc_data(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched and then rejected by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.minimum
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.soft_reject),
        payment_command_states=["S_INIT", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_then_receiver_aborts_for_sending_additional_kyc_data(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with minimum valid kyc data and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched by the stub wallet application and 0 balance in the target wallet application.
    3. Setup the stub wallet applicatoin to abort the payment command if receiver requests additional KYC data (soft match).
    4. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    5. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SEND", "S_SOFT", "R_ABORT"]
    6. Expect sender and receiver accounts' balances are not changed.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold},
            kyc_data=target_kyc.soft_match,
            reject_additional_kyc_data_request=True,
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.minimum),
        payment_command_states=["S_INIT", "R_SOFT", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_sender_and_receiver_kyc_data_are_soft_match_then_accepted_after_reviewing_additional_kyc_data(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the target wallet application and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched and then accepted by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"]
    5. Expect send payment success; receiver account balance increased by the amount sent; sender account balance decreased by the amount sent.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.soft_match
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.soft_match),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "READY"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_and_accepted_receiver_kyc_data_is_rejected(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the target wallet application and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be rejected by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.soft_match
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.reject),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def test_receive_payment_meets_travel_rule_threshold_sender_kyc_data_is_soft_match_and_accepted_receiver_kyc_data_is_soft_match_and_rejected(
    currency: str, travel_rule_threshold: int, target_client: RestClient, stub_client: RestClient
) -> None:
    """
    Test Plan:

    1. Create sender account with kyc data that will be soft matched and then accepted by the target wallet application and enough balance in the stub wallet application.
    2. Create receiver account with kyc data that will be soft matched and then rejected by the stub wallet application and 0 balance in the target wallet application.
    3. Send payment from sender account to receiver account, amount is equal to travel_rule threshold.
    4. Wait for stub wallet application account events include payment command states: ["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"]
    5. Expect sender and receiver accounts' balances are not changed.
    """

    target_kyc = await target_client.get_kyc_sample()
    stub_kyc = await stub_client.get_kyc_sample()
    await receive_payment_meets_travel_rule_threshold(
        sender=await stub_client.create_account(
            balances={currency: travel_rule_threshold}, kyc_data=target_kyc.soft_match
        ),
        receiver=await target_client.create_account(kyc_data=stub_kyc.soft_reject),
        payment_command_states=["S_INIT", "R_SOFT", "S_SOFT_SEND", "R_SEND", "S_SOFT", "R_SOFT_SEND", "S_ABORT"],
        currency=currency,
        amount=travel_rule_threshold,
    )


async def receive_payment_meets_travel_rule_threshold(
    sender: AccountResource,
    receiver: AccountResource,
    payment_command_states: List[str],
    currency: str,
    amount: int,
    sender_reject_additional_kyc_data_request: bool = False,
) -> None:
    sender_initial = await sender.balance(currency)
    receiver_initial = await receiver.balance(currency)

    payee = await receiver.generate_account_identifier()
    await sender.send_payment(currency, amount, payee)

    async def match_exchange_states() -> None:
        states = []
        events = await sender.events()
        for e in events:
            if e.type in ["created_payment_command", "updated_payment_command"]:
                payment_object = json.loads(e.data)["payment_object"]
                payment = offchain.from_dict(payment_object, offchain.PaymentObject)
                states.append(offchain.payment_state.MACHINE.match_state(payment).id)
        assert states == payment_command_states

    await wait_for(match_exchange_states)

    if payment_command_states[-1] == "READY":
        await wait_for_balance(sender, currency, sender_initial - amount)
        await wait_for_balance(receiver, currency, receiver_initial + amount)
    else:
        await wait_for_balance(sender, currency, sender_initial)
        await wait_for_balance(receiver, currency, receiver_initial)
