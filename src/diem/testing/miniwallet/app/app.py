# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import List, Tuple, Dict, Optional, Any, Callable, Awaitable
from json.decoder import JSONDecodeError
from .store import InMemoryStore, NotFoundError
from .pending_account import PENDING_INBOUND_ACCOUNT_ID
from .diem_account import DiemAccount
from .models import Subaddress, Account, Transaction, Event, KycSample, PaymentCommand, ReferenceID
from .event_puller import EventPuller
from .json_input import JsonInput
from ... import LocalAccount

from .... import jsonrpc, offchain, utils, identifier
from ....offchain import KycDataObject
from diem.jsonrpc import AsyncClient
from diem.diem_types import AccountAddress

import logging, numpy, asyncio, uuid, functools


class App:
    def __init__(
        self,
        account: LocalAccount,
        child_accounts: List[LocalAccount],
        client: AsyncClient,
        name: str,
        logger: logging.Logger,
    ) -> None:
        self.logger = logger
        self.diem_account = DiemAccount(account, child_accounts, client)
        self.store = InMemoryStore()
        self.store.create(Account, id=PENDING_INBOUND_ACCOUNT_ID)
        self.diem_client = client
        self.offchain = offchain.Client(account.account_address, client, account.hrp)
        self.kyc_sample: KycSample = KycSample.gen(name)
        self.event_puller = EventPuller(client=client, store=self.store, hrp=account.hrp, logger=logger)
        self.bg_tasks: List[Callable[[], Awaitable[None]]] = []
        self.dual_attestation_txn_senders: Dict[str, Callable[[Transaction], Awaitable[None]]] = {}

    async def create_account(self, data: JsonInput) -> Dict[str, str]:
        account = self.store.create(
            Account,
            kyc_data=await data.get_nullable("kyc_data", dict, self._validate_kyc_data),
            # reject_additional_kyc_data_request is used for setting up rejecting
            # additional_kyc_data request in offchain PaymentCommand processing.
            reject_additional_kyc_data_request=await data.get_nullable("reject_additional_kyc_data_request", bool),
            # disable_background_tasks disables background task processing in the App for the account,
            # it is used for testing offchain api.
            disable_background_tasks=await data.get_nullable("disable_background_tasks", bool),
            diem_id_domain=next(iter(await self.diem_account.diem_id_domains()), None),
        )
        balances = await data.get_nullable("balances", dict)
        if balances:
            for currency, amount in balances.items():
                data = JsonInput({"currency": currency, "amount": amount})
                self.store.create(
                    Transaction,
                    account_id=account.id,
                    currency=await data.get("currency", str, self._validate_currency_code),
                    amount=await data.get("amount", int, self._validate_amount),
                    status=Transaction.Status.completed,
                    type=Transaction.Type.deposit,
                )
        return {"id": account.id}

    async def create_account_payment(self, account_id: str, data: JsonInput) -> Dict[str, Any]:
        account = self.store.find(Account, id=account_id)
        payee = await data.get("payee", str)
        payee_account_id, subaddress_hex, reference_id, account_identifier = (None, None, None, None)
        try:
            if identifier.diem_id.is_diem_id(payee):
                domain = identifier.diem_id.get_vasp_identifier_from_diem_id(payee)
                if domain in await self.diem_account.diem_id_domains():
                    diem_user_id = identifier.diem_id.get_user_identifier_from_diem_id(payee)
                    payee_account_id = self.store.find(Account, id=diem_user_id).id
                else:
                    reference_id = self._create_reference_id(account.id)
                    account_identifier = await self._exchange_diem_id(account, payee, reference_id)
            else:
                if await self.offchain.is_my_account_id(payee):
                    _, subaddress = self.diem_account.decode_account_identifier(payee)
                    sub = self.store.find(Subaddress, subaddress_hex=utils.hex(subaddress))
                    payee_account_id = sub.account_id
                else:
                    subaddress_hex = self._gen_subaddress(account.id).hex()
                    await self._validate_account_identifier(payee, "'payee' is invalid account identifier")
                    account_identifier = payee
        except ValueError as e:
            raise ValueError("'payee' is invalid: %s" % e)

        txn = self.store.create(
            Transaction,
            account_id=account.id,
            currency=await data.get("currency", str, self._validate_currency_code),
            amount=await data.get("amount", int, self._validate_amount),
            status=Transaction.Status.pending,
            type=Transaction.Type.sent_payment,
            payee=payee,
            subaddress_hex=subaddress_hex,
            reference_id=reference_id,
            payee_account_identifier=account_identifier,
            payee_account_id=payee_account_id,
            before_create=self._validate_account_balance,
        )
        return {"id": txn.id}

    def create_account_identifier(self, account_id: str, data: JsonInput) -> Dict[str, str]:
        self.store.find(Account, id=account_id)
        diem_acc_id = self.diem_account.account_identifier(self._gen_subaddress(account_id))
        return {"account_identifier": diem_acc_id}

    def get_account_balances(self, account_id: str) -> Dict[str, int]:
        self.store.find(Account, id=account_id)
        return self._balances(account_id)

    def get_account_events(self, account_id: str) -> List[Event]:
        return self.store.find_all(Event, account_id=account_id)

    def add_dual_attestation_txn_sender(self, version: str, sender: Callable[[Transaction], Awaitable[None]]) -> None:
        self.dual_attestation_txn_senders[version] = sender

    def add_bg_task(self, task: Callable[[], Awaitable[None]]) -> None:
        self.bg_tasks.append(task)

    async def start_worker(self, delay: float = 0.05) -> asyncio.Task:
        await self.event_puller.add_received_events_key(self.diem_account._account.account_address)
        for child_account in self.diem_account._child_accounts:
            await self.event_puller.add_received_events_key(child_account.account_address)
        await self.event_puller.head()
        self.add_bg_task(self.event_puller.process)
        self.add_bg_task(self._send_pending_payments)
        self.add_bg_task(functools.partial(asyncio.sleep, delay))

        async def worker() -> None:
            while True:
                try:
                    await asyncio.gather(*[t() for t in self.bg_tasks])
                except asyncio.CancelledError:
                    # when application is shutting down, tasks maybe cancelled.
                    # ignore the error and shutdown the worker.
                    return
                except Exception as e:
                    self.logger.exception(e)

        return asyncio.create_task(worker())

    async def txn_metadata(self, txn: Transaction) -> Tuple[bytes, bytes]:
        if await self.offchain.is_under_dual_attestation_limit(txn.currency, txn.amount):
            if txn.refund_diem_txn_version and txn.refund_reason:
                return self.diem_account.refund_metadata(txn.refund_diem_txn_version, txn.refund_reason)  # pyre-ignore
            if txn.subaddress_hex:
                return self.diem_account.general_metadata(txn.subaddress(), str(txn.payee))
            if txn.reference_id:
                return self.diem_account.payment_metadata(str(txn.reference_id))
        elif txn.reference_id:
            cmd = self.store.find(PaymentCommand, reference_id=txn.reference_id)
            return self.diem_account.travel_metadata(cmd.to_offchain_command())
        raise ValueError("could not create diem payment transacton metadata: %s" % txn)

    async def _send_pending_payments(self) -> None:
        txns = self.store.find_all(Transaction, status=Transaction.Status.pending)
        await asyncio.gather(*[self._send_pending_payment(txn) for txn in txns])

    async def _send_pending_payment(self, txn: Transaction) -> None:
        if self.store.find(Account, id=txn.account_id).disable_background_tasks:
            self.logger.debug("account bg tasks disabled, ignore %s", txn)
            return
        self.logger.info("send pending payment %s", txn)
        try:
            if txn.payee_account_id:
                self._send_internal_payment_txn(txn)
            else:
                await self._send_external_payment_txn(txn)
        except jsonrpc.JsonRpcError as e:
            msg = "ignore error %s when sending transaction %s, retry later"
            self.logger.info(msg, e, txn, exc_info=True)
        except Exception as e:
            msg = "send pending transaction failed with %s, cancel transaction %s."
            self.logger.error(msg, e, txn, exc_info=True)
            self.store.update(txn, status=Transaction.Status.canceled, cancel_reason=str(e))

    def _send_internal_payment_txn(self, txn: Transaction) -> None:
        self.store.create(
            Transaction,
            account_id=txn.payee_account_id,
            currency=txn.currency,
            amount=txn.amount,
            status=Transaction.Status.completed,
            type=Transaction.Type.sent_payment,
        )
        self.store.update(txn, status=Transaction.Status.completed)

    async def _send_external_payment_txn(self, txn: Transaction) -> None:
        if await self.offchain.is_under_dual_attestation_limit(txn.currency, txn.amount):
            await self.send_diem_p2p_transaction(txn)
        else:
            await self.dual_attestation_txn_senders["v2"](txn)

    async def send_diem_p2p_transaction(self, txn: Transaction, address: Optional[AccountAddress] = None) -> None:
        if not txn.signed_transaction:
            signed_txn = await self.diem_account.submit_p2p(txn, await self.txn_metadata(txn), by_address=address)
            self.store.update(txn, signed_transaction=signed_txn.bcs_serialize().hex())
        await self._wait_for_diem_txn(txn)

    async def _wait_for_diem_txn(self, txn: Transaction) -> None:
        try:
            diem_txn = await self.diem_client.wait_for_transaction(str(txn.signed_transaction), timeout_secs=0.1)
            self.store.update(txn, status=Transaction.Status.completed, diem_transaction_version=diem_txn.version)
        except jsonrpc.WaitForTransactionTimeout as e:
            self.logger.info("wait for txn(%s) timeout: %s, re-check later", txn, e)
        except jsonrpc.TransactionHashMismatchError as e:
            self.logger.warn("txn(%s) hash mismatched(%s), re-send diem p2p txn", txn, e)
            txn.signed_transaction = None
            await self.send_diem_p2p_transaction(txn)
        except (jsonrpc.TransactionExpired, jsonrpc.TransactionExecutionFailed) as e:
            self.logger.error("txn(%s) execution expired / failed(%s), canceled", txn, e)
            reason = "something went wrong with transaction execution: %s" % e
            self.store.update(txn, status=Transaction.Status.canceled, cancel_reason=reason)

    async def _exchange_diem_id(self, payer: Account, diem_id: str, reference_id: str) -> str:
        address = await self._find_diem_id_account_address(diem_id)
        response = await self.offchain.ref_id_exchange_request(
            sender=str(payer.diem_id),
            sender_address=self.diem_account.account_identifier(),
            receiver=diem_id,
            reference_id=reference_id,
            counterparty_account_identifier=identifier.encode_account(address, None, self.diem_account.hrp),
            sign=self.diem_account.sign_by_compliance_key,
        )
        err_msg = "invalid reference_id_exchange response: %s" % response
        if response.result:
            address = response.result.get("receiver_address")
            await self._validate_account_identifier(address, err_msg)
            return address
        raise ValueError(err_msg)

    async def _validate_kyc_data(self, name: str, val: Dict[str, Any]) -> None:
        try:
            offchain.from_dict(val, KycDataObject)
        except (JSONDecodeError, offchain.types.FieldError) as e:
            raise ValueError("%r must be JSON-encoded KycDataObject: %s" % (name, e))

    async def _validate_currency_code(self, name: str, val: str) -> None:
        try:
            await self.offchain.validate_currency_code(val)
        except ValueError:
            raise ValueError("%r is invalid currency code: %s" % (name, val))

    async def _validate_account_identifier(self, val: str, err_msg: str) -> None:
        account_address, _ = self.diem_account.decode_account_identifier(val)
        account = await self.diem_client.get_account(account_address)
        if account is None:
            raise ValueError(err_msg + ", account address: %s" % account_address.to_hex())

    async def _validate_amount(self, name: str, val: int) -> None:
        if val < 0:
            raise ValueError("%r value must be greater than or equal to zero" % name)
        try:
            numpy.uint64(val)
        except OverflowError:
            raise ValueError("%r value is too big" % name)

    def _validate_account_balance(self, txn: Dict[str, Any]) -> None:
        if txn.get("payee"):
            balance = self._balances(txn["account_id"]).get(txn["currency"], 0)
            if balance < txn["amount"]:
                raise ValueError("account balance not enough: %s (%s)" % (balance, txn))

    def _balances(self, account_id: str) -> Dict[str, int]:
        ret = {}
        for txn in self.store.find_all(Transaction, account_id=account_id):
            if txn.status != Transaction.Status.canceled:
                ret[txn.currency] = ret.get(txn.currency, 0) + txn.balance_amount()
        return ret

    def _gen_subaddress(self, account_id: str) -> bytes:
        sub = self.store.next_id().to_bytes(8, byteorder="big")
        self.store.create(Subaddress, account_id=account_id, subaddress_hex=sub.hex())
        return sub

    def validate_unique_reference_id(self, reference_id: str) -> None:
        try:
            duplicate_ref_id = self.store.find(ReferenceID, reference_id=reference_id)
            raise ValueError(f"{reference_id} exists for account ID {duplicate_ref_id.account_id}")
        except NotFoundError:
            return

    async def _find_diem_id_account_address(self, diem_id: str) -> str:
        domain = identifier.diem_id.get_vasp_identifier_from_diem_id(diem_id)
        domain_map = await self.diem_client.get_diem_id_domain_map()
        account_address = domain_map.get(domain)
        if account_address is None:
            raise ValueError("could not find onchain account address by diem id: %s" % diem_id)
        return account_address

    def _create_reference_id(self, account_id: str) -> str:
        while True:
            reference_id = str(uuid.uuid4())
            try:
                self.store.create(
                    ReferenceID,
                    before_create=lambda data: self.validate_unique_reference_id(data["reference_id"]),
                    account_id=account_id,
                    reference_id=reference_id,
                )
                return reference_id
            except ValueError:
                continue
