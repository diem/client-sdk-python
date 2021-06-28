# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import List, Tuple, Dict, Optional, Any, Callable
import uuid
from json.decoder import JSONDecodeError
from .store import InMemoryStore, NotFoundError
from .pending_account import PENDING_INBOUND_ACCOUNT_ID
from .diem_account import DiemAccount
from .models import Subaddress, Account, Transaction, Event, KycSample, PaymentCommand, ReferenceID
from .event_puller import EventPuller
from .json_input import JsonInput
from ... import LocalAccount
from .... import jsonrpc, offchain, utils, identifier
from ....offchain import KycDataObject, ErrorCode
import threading, logging, numpy, time


class App:
    def __init__(
        self,
        account: LocalAccount,
        child_accounts: List[LocalAccount],
        client: jsonrpc.Client,
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
        self.bg_tasks: List[Callable[[], None]] = []
        self.dual_attestation_txn_senders: Dict[str, Callable[[Transaction], None]] = {}

    def create_account(self, data: JsonInput) -> Dict[str, str]:
        account = self.store.create(
            Account,
            kyc_data=data.get_nullable("kyc_data", dict, self._validate_kyc_data),
            # reject_additional_kyc_data_request is used for setting up rejecting
            # additional_kyc_data request in offchain PaymentCommand processing.
            reject_additional_kyc_data_request=data.get_nullable("reject_additional_kyc_data_request", bool),
            # disable_background_tasks disables background task processing in the App for the account,
            # it is used for testing offchain api.
            disable_background_tasks=data.get_nullable("disable_outbound_request", bool),
        )
        if len(self.diem_account.diem_id_domains()) != 0:
            diem_id = identifier.diem_id.create_diem_id(str(account.id), self.diem_account.diem_id_domains()[0])
            self.store.update(account, diem_id=diem_id)
        balances = data.get_nullable("balances", dict)
        if balances:
            for c, a in balances.items():
                self._create_transaction(
                    account.id,
                    Transaction.Status.completed,
                    JsonInput({"currency": c, "amount": a}),
                    type=Transaction.Type.deposit,
                )
        return {"id": account.id}

    def create_account_payment(self, account_id: str, data: JsonInput) -> Dict[str, Any]:
        self.store.find(Account, id=account_id)
        subaddress_hex = None
        payee = data.get("payee", str)
        if identifier.diem_id.is_diem_id(payee):
            self._validate_diem_id(payee)
        else:
            self._validate_account_identifier("payee", payee)
            subaddress_hex = None if self.offchain.is_my_account_id(payee) else self._gen_subaddress(account_id).hex()

        txn = self._create_transaction(
            account_id,
            Transaction.Status.pending,
            data,
            type=Transaction.Type.sent_payment,
            payee=payee,
            subaddress_hex=subaddress_hex,
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

    def add_dual_attestation_txn_sender(self, version: str, sender: Callable[[Transaction], None]) -> None:
        self.dual_attestation_txn_senders[version] = sender

    def add_bg_task(self, task: Callable[[], None]) -> None:
        self.bg_tasks.append(task)

    def start_bg_worker_thread(self, delay: float = 0.1) -> None:
        self.event_puller.add_received_events_key(self.diem_account._account.account_address)
        for child_account in self.diem_account._child_accounts:
            self.event_puller.add_received_events_key(child_account.account_address)
        self.event_puller.head()
        self.add_bg_task(self.event_puller.process)
        self.add_bg_task(self._send_pending_payments)

        def worker() -> None:
            while True:
                for t in self.bg_tasks:
                    try:
                        t()
                    except Exception as e:
                        self.logger.exception(e)
                time.sleep(delay)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def txn_metadata(self, txn: Transaction) -> Tuple[bytes, bytes]:
        if self.offchain.is_under_dual_attestation_limit(txn.currency, txn.amount):
            if txn.refund_diem_txn_version and txn.refund_reason:
                return self.diem_account.refund_metadata(txn.refund_diem_txn_version, txn.refund_reason)  # pyre-ignore
            if txn.subaddress_hex:
                return self.diem_account.general_metadata(txn.subaddress(), str(txn.payee))
            if txn.reference_id is not None:
                return self.diem_account.payment_metadata(str(txn.reference_id))
        elif txn.reference_id:
            cmd = self.store.find(PaymentCommand, reference_id=txn.reference_id)
            return self.diem_account.travel_metadata(cmd.to_offchain_command())
        raise ValueError("could not create diem payment transacton metadata: %s" % txn)

    def _send_pending_payments(self) -> None:
        for txn in self.store.find_all(Transaction, status=Transaction.Status.pending):
            if self.store.find(Account, id=txn.account_id).disable_background_tasks:
                self.logger.debug("account bg tasks disabled, ignore %s", txn)
                continue
            self.logger.info("processing %s", txn)
            try:
                if identifier.diem_id.is_diem_id(str(txn.payee)):
                    vasp_identifier = identifier.diem_id.get_vasp_identifier_from_diem_id(str(txn.payee))
                    if vasp_identifier in self.diem_account.diem_id_domains():
                        self._send_internal_payment_txn(txn)
                    else:
                        self._send_external_payment_txn(txn)
                elif self.offchain.is_my_account_id(str(txn.payee)):
                    self._send_internal_payment_txn(txn)
                else:
                    self._send_external_payment_txn(txn)
            except jsonrpc.JsonRpcError as e:
                msg = "ignore error %s when sending transaction %s, retry later"
                self.logger.info(msg % (e, txn), exc_info=True)
            except Exception as e:
                msg = "send pending transaction failed with %s, cancel transaction %s."
                self.logger.error(msg % (e, txn), exc_info=True)
                self.store.update(txn, status=Transaction.Status.canceled, cancel_reason=str(e))

    def _send_internal_payment_txn(self, txn: Transaction) -> None:
        # TODO diem_id: handle DiemID case for internal
        _, payee_subaddress = self.diem_account.decode_account_identifier(str(txn.payee))
        subaddress = self.store.find(Subaddress, subaddress_hex=utils.hex(payee_subaddress))
        self.store.create(
            Transaction,
            account_id=subaddress.account_id,
            currency=txn.currency,
            amount=txn.amount,
            status=Transaction.Status.completed,
            type=Transaction.Type.sent_payment,
        )
        self.store.update(txn, status=Transaction.Status.completed)

    def _send_external_payment_txn(self, txn: Transaction) -> None:
        if txn.signed_transaction:
            try:
                diem_txn = self.diem_client.wait_for_transaction(str(txn.signed_transaction), timeout_secs=0.1)
                self.store.update(txn, status=Transaction.Status.completed, diem_transaction_version=diem_txn.version)
            except jsonrpc.WaitForTransactionTimeout as e:
                self.logger.debug("wait for txn(%s) timeout: %s", txn, e)
            except jsonrpc.TransactionHashMismatchError as e:
                self.logger.warn("txn(%s) hash mismatched(%s), re-submit", txn, e)
                self.store.update(txn, signed_transaction=self.diem_account.submit_p2p(txn, self.txn_metadata(txn)))
            except (jsonrpc.TransactionExpired, jsonrpc.TransactionExecutionFailed) as e:
                self.logger.error("txn(%s) execution expired / failed(%s), canceled", txn, e)
                reason = "something went wrong with transaction execution: %s" % e
                self.store.update(txn, status=Transaction.Status.canceled, cancel_reason=reason)
        else:
            self._start_external_payment_txn(txn)

    def _start_external_payment_txn(self, txn: Transaction) -> None:  # noqa: C901
        if identifier.diem_id.is_diem_id(str(txn.payee)):
            reference_id = self._create_reference_id(txn)
            try:
                vasp_identifier = identifier.diem_id.get_vasp_identifier_from_diem_id(str(txn.payee))
                domain_map = self.diem_client.get_diem_id_domain_map()
                diem_id_address = domain_map.get(vasp_identifier)
                if diem_id_address is None:
                    raise ValueError(f"Diem ID domain {vasp_identifier} was not found")
                self.store.update(txn, reference_id=reference_id)
                response = self.offchain.ref_id_exchange_request(
                    sender=str(self.store.find(Account, id=txn.account_id).diem_id),
                    sender_address=self.diem_account.account_identifier(),
                    receiver=str(txn.payee),
                    reference_id=reference_id,
                    counterparty_account_identifier=identifier.encode_account(
                        diem_id_address, None, self.diem_account.hrp
                    ),
                    sign=self.diem_account.sign_by_compliance_key,
                )
                receiver_address, _ = self.diem_account.decode_account_identifier(
                    response.result.get("receiver_address")  # pyre-ignore
                )
                self.store.update(txn, payee_onchain_address=receiver_address.to_hex())
            except offchain.Error as e:
                if e.obj.code == ErrorCode.duplicate_reference_id:
                    return
        if self.offchain.is_under_dual_attestation_limit(txn.currency, txn.amount):
            if not txn.signed_transaction:
                signed_txn = self.diem_account.submit_p2p(txn, self.txn_metadata(txn))
                self.store.update(txn, signed_transaction=signed_txn)
        else:
            self.dual_attestation_txn_senders["v2"](txn)

    def _create_transaction(
        self,
        account_id: str,
        status: str,
        data: JsonInput,
        type: Transaction.Type,
        payee: Optional[str] = None,
        subaddress_hex: Optional[str] = None,
    ) -> Transaction:
        return self.store.create(
            Transaction,
            account_id=account_id,
            currency=data.get("currency", str, self._validate_currency_code),
            amount=data.get("amount", int, self._validate_amount),
            payee=payee,
            status=status,
            type=type,
            subaddress_hex=subaddress_hex,
            before_create=self._validate_account_balance,
        )

    def _validate_kyc_data(self, name: str, val: Dict[str, Any]) -> None:
        try:
            offchain.from_dict(val, KycDataObject)
        except (JSONDecodeError, offchain.types.FieldError) as e:
            raise ValueError("%r must be JSON-encoded KycDataObject: %s" % (name, e))

    def _validate_currency_code(self, name: str, val: str) -> None:
        try:
            self.offchain.validate_currency_code(val)
        except ValueError:
            raise ValueError("%r is invalid currency code: %s" % (name, val))

    def _validate_account_identifier(self, name: str, val: str) -> None:
        try:
            account_address, _ = self.diem_account.decode_account_identifier(val)
            self.diem_client.must_get_account(account_address)
        except ValueError as e:
            raise ValueError("%r is invalid account identifier: %s" % (name, e))

    def _validate_amount(self, name: str, val: int) -> None:
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

    # Check the payee diem ID can be found in the domain map
    # Check if payee is in the same wallet, the receiver account exists
    def _validate_diem_id(self, diem_id: str) -> None:
        payee_vasp_identifier = identifier.diem_id.get_vasp_identifier_from_diem_id(diem_id)
        domain_map = self.diem_client.get_diem_id_domain_map()
        payee_onchain_address = domain_map.get(payee_vasp_identifier)
        if payee_onchain_address is None:
            raise ValueError(f"Diem ID domain {payee_vasp_identifier} was not found")
        if payee_vasp_identifier in self.diem_account.diem_id_domains():
            self.store.find(Account, diem_id=diem_id)

    def _create_reference_id(self, txn: Transaction) -> str:
        while True:
            reference_id = str(uuid.uuid4())
            try:
                self.store.create(
                    ReferenceID,
                    before_create=lambda data: self.validate_unique_reference_id(data["reference_id"]),
                    account_id=txn.account_id,
                    reference_id=reference_id,
                )
                return reference_id
            except ValueError:
                continue
