# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import asdict
from typing import List, Tuple, Dict, Optional, Any
from json.decoder import JSONDecodeError
from .store import InMemoryStore, NotFoundError
from .diem_account import DiemAccount
from .models import PaymentUri, Subaddress, Account, Transaction, Event, KycSample, Payment, PaymentCommand
from .event_puller import EventPuller
from .json_input import JsonInput
from ... import LocalAccount
from .... import jsonrpc, offchain, utils, identifier
from ....offchain import KycDataObject, Status, AbortCode, CommandResponseObject
import threading, logging, numpy


class Base:
    def __init__(self, account: LocalAccount, client: jsonrpc.Client, name: str, logger: logging.Logger) -> None:
        self.logger = logger
        self.diem_account = DiemAccount(account, client)
        self.store = InMemoryStore()
        self.offchain = offchain.Client(account.account_address, client, account.hrp)
        self.kyc_sample: KycSample = KycSample.gen(name)
        self.event_puller = EventPuller(client=client, store=self.store, hrp=account.hrp, logger=logger)
        self.event_puller.add(account.account_address)
        self.event_puller.head()

    def _validate_kyc_data(self, name: str, val: str) -> None:
        try:
            offchain.from_json(val, KycDataObject)
        except (JSONDecodeError, offchain.types.FieldError) as e:
            raise ValueError("%r must be JSON-encoded KycDataObject: %s" % (name, e))

    def _validate_currency_code(self, name: str, val: str) -> None:
        try:
            self.offchain.validate_currency_code(val)
        except ValueError:
            raise ValueError("%r is invalid currency code: %s" % (name, val))

    def _validate_account_identifier(self, name: str, val: str) -> None:
        try:
            account_address, _ = self.diem_account.account.decode_account_identifier(val)
            self.diem_account.client.must_get_account(account_address)
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

    def _gen_subaddress(self, account_id: str) -> Subaddress:
        sub = self.store.next_id().to_bytes(8, byteorder="big")
        return self.store.create(Subaddress, account_id=account_id, subaddress_hex=sub.hex())

    def _txn_metadata(self, txn: Transaction) -> Tuple[bytes, bytes]:
        if self.offchain.is_under_dual_attestation_limit(txn.currency, txn.amount):
            if txn.refund_diem_txn_version and txn.refund_reason:
                return self.diem_account.refund_metadata(txn.refund_diem_txn_version, txn.refund_reason)  # pyre-ignore
            if txn.subaddress_hex:
                return self.diem_account.general_metadata(txn.subaddress(), str(txn.payee))
        elif txn.reference_id:
            cmd = self.store.find(PaymentCommand, reference_id=txn.reference_id)
            return self.diem_account.travel_metadata(cmd.to_offchain_command())
        raise ValueError("could not create diem payment transacton metadata: %s" % txn)


class OffChainAPI(Base):
    def offchain_api(self, request_sender_address: str, request_bytes: bytes) -> CommandResponseObject:
        request = self.offchain.deserialize_inbound_request(request_sender_address, request_bytes)
        getattr(self, "_handle_offchain_%s" % utils.to_snake(request.command_type))(request_sender_address, request)
        return offchain.reply_request(cid=request.cid)

    def jws_serialize(self, resp: CommandResponseObject) -> bytes:
        return offchain.jws.serialize(resp, self.diem_account.account.compliance_key.sign)

    def _handle_offchain_payment_command(
        self, request_sender_address: str, request: offchain.CommandRequestObject
    ) -> None:
        new_offchain_cmd = self.offchain.process_inbound_payment_command_request(request_sender_address, request)
        try:
            cmd = self.store.find(PaymentCommand, reference_id=new_offchain_cmd.reference_id())
            if new_offchain_cmd != cmd.to_offchain_command():
                self._update_payment_command(cmd, new_offchain_cmd)
        except NotFoundError:
            subaddress = utils.hex(new_offchain_cmd.my_subaddress(self.diem_account.account.hrp))
            account_id = self.store.find(Subaddress, subaddress_hex=subaddress).account_id
            self._create_payment_command(account_id, new_offchain_cmd, validate=True)

    def _create_payment_command(self, account_id: str, cmd: offchain.PaymentCommand, validate: bool = False) -> None:
        self.store.create(
            PaymentCommand,
            before_create=lambda _: cmd.validate(None) if validate else None,
            account_id=account_id,
            is_sender=cmd.is_sender(),
            reference_id=cmd.reference_id(),
            is_inbound=cmd.is_inbound(),
            cid=cmd.id(),
            payment_object=asdict(cmd.payment),
        )

    def _update_payment_command(
        self, cmd: PaymentCommand, offchain_cmd: offchain.PaymentCommand, validate: bool = False
    ) -> None:
        self.store.update(
            cmd,
            before_update=lambda _: offchain_cmd.validate(cmd.to_offchain_command()) if validate else None,
            cid=offchain_cmd.id(),
            is_inbound=offchain_cmd.is_inbound(),
            is_abort=offchain_cmd.is_abort(),
            is_ready=offchain_cmd.is_both_ready(),
            payment_object=asdict(offchain_cmd.payment),
        )


class BackgroundTasks(OffChainAPI):
    def start_sync(self, delay: float = 0.1) -> None:
        try:
            self._process_offchain_commands()
            self._send_pending_payments()
            self.event_puller.fetch(self.event_puller.save_payment_txn)
        except Exception as e:
            self.logger.exception(e)
            # Exponential backoff for the delay to slow down the background tasks execution
            # cycle and reduce the duplicated error logs.
            delay = delay * 2

        if threading.main_thread().is_alive():
            threading.Timer(delay, self.start_sync, args=[delay]).start()

    def _send_pending_payments(self) -> None:
        for txn in self.store.find_all(Transaction, status=Transaction.Status.pending):
            self.logger.info("processing %s", txn)
            try:
                if self.offchain.is_my_account_id(str(txn.payee)):
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
        _, payee_subaddress = self.diem_account.account.decode_account_identifier(str(txn.payee))
        subaddress = self.store.find(Subaddress, subaddress_hex=utils.hex(payee_subaddress))
        self.store.create(
            Transaction,
            account_id=subaddress.account_id,
            currency=txn.currency,
            amount=txn.amount,
            status=Transaction.Status.completed,
        )
        self.store.update(txn, status=Transaction.Status.completed)

    def _send_external_payment_txn(self, txn: Transaction) -> None:
        if txn.signed_transaction:
            try:
                diem_txn = self.diem_account.client.wait_for_transaction(str(txn.signed_transaction), timeout_secs=0.1)
                self.store.update(txn, status=Transaction.Status.completed, diem_transaction_version=diem_txn.version)
            except jsonrpc.WaitForTransactionTimeout as e:
                self.logger.debug("wait for txn(%s) timeout: %s", txn, e)
            except jsonrpc.TransactionHashMismatchError as e:
                self.logger.warn("txn(%s) hash mismatched(%s), re-submit", txn, e)
                self.store.update(txn, signed_transaction=self.diem_account.submit_p2p(txn, self._txn_metadata(txn)))
            except (jsonrpc.TransactionExpired, jsonrpc.TransactionExecutionFailed) as e:
                self.logger.error("txn(%s) execution expired / failed(%s), canceled", txn, e)
                reason = "something went wrong with transaction execution: %s" % e
                self.store.update(txn, status=Transaction.Status.canceled, cancel_reason=reason)
        else:
            self._start_external_payment_txn(txn)

    def _start_external_payment_txn(self, txn: Transaction) -> None:
        if not txn.subaddress_hex:
            self.store.update(txn, subaddress_hex=self._gen_subaddress(txn.account_id).subaddress_hex)
        if self.offchain.is_under_dual_attestation_limit(txn.currency, txn.amount):
            if not txn.signed_transaction:
                signed_txn = self.diem_account.submit_p2p(txn, self._txn_metadata(txn))
                self.store.update(txn, signed_transaction=signed_txn)
        else:
            if txn.reference_id:
                cmd = self.store.find(PaymentCommand, reference_id=txn.reference_id)
                if cmd.is_sender:
                    if cmd.is_abort:
                        status = Transaction.Status.canceled
                        self.store.update(txn, status=status, cancel_reason="exchange kyc data abort")
                    elif cmd.is_ready:
                        signed_txn = self.diem_account.submit_p2p(txn, self._txn_metadata(txn))
                        self.store.update(txn, signed_transaction=signed_txn)
            else:
                account = self.store.find(Account, id=txn.account_id)
                command = offchain.PaymentCommand.init(
                    sender_account_id=self.diem_account.account.account_identifier(txn.subaddress()),
                    sender_kyc_data=account.kyc_data_object(),
                    currency=txn.currency,
                    amount=txn.amount,
                    receiver_account_id=str(txn.payee),
                )
                self._create_payment_command(txn.account_id, command)
                self.store.update(txn, reference_id=command.reference_id())
                self._send_offchain_command(command)

    def _process_offchain_commands(self) -> None:
        cmds = self.store.find_all(PaymentCommand, is_inbound=True, is_abort=False, is_ready=False, process_error=None)
        for cmd in cmds:
            try:
                offchain_cmd = cmd.to_offchain_command()
                action = offchain_cmd.follow_up_action()
                if action:
                    fn = getattr(self, "_offchain_action_%s" % action.value)
                    new_offchain_cmd = fn(cmd.account_id, offchain_cmd)
                    self._update_payment_command(cmd, new_offchain_cmd)
                    self._send_offchain_command(new_offchain_cmd)
            except Exception as e:
                self.logger.exception(e)
                self.store.update(cmd, process_error=str(e))

    def _send_offchain_command(self, command: offchain.Command) -> None:
        """send offchain command with retries

        We only do limited in process retries, as we are expecting counterparty service
        should be available in dev / testing environment, and fail immediately if counterparty
        service is not available.
        In production environment, you may need implement better retry system for handling
        counterparty service temporarily not available case.
        """

        retry = jsonrpc.Retry(5, 0.2, Exception)
        retry.execute(lambda: self.offchain.send_command(command, self.diem_account.account.compliance_key.sign))

    def _offchain_action_evaluate_kyc_data(self, account_id: str, cmd: offchain.PaymentCommand) -> offchain.Command:
        op_kyc_data = cmd.counterparty_actor_obj().kyc_data
        if op_kyc_data is None or self.kyc_sample.match_kyc_data("reject", op_kyc_data):
            return self._new_reject_kyc_data(cmd, "KYC data is rejected")
        elif self.kyc_sample.match_any_kyc_data(["soft_match", "soft_reject"], op_kyc_data):
            return cmd.new_command(status=Status.soft_match)
        return self._ready_for_settlement(account_id, cmd)

    def _offchain_action_clear_soft_match(self, account_id: str, cmd: offchain.PaymentCommand) -> offchain.Command:
        account = self.store.find(Account, id=account_id)
        if account.reject_additional_kyc_data_request:
            return self._new_reject_kyc_data(cmd, "no need additional KYC data")
        return cmd.new_command(additional_kyc_data="{%r: %r}" % ("account_id", account_id))

    def _offchain_action_review_kyc_data(self, account_id: str, cmd: offchain.PaymentCommand) -> offchain.Command:
        op_kyc_data = cmd.counterparty_actor_obj().kyc_data
        if op_kyc_data is None or self.kyc_sample.match_kyc_data("soft_reject", op_kyc_data):
            return self._new_reject_kyc_data(cmd, "KYC data review result is reject")
        return self._ready_for_settlement(account_id, cmd)

    def _new_reject_kyc_data(self, cmd: offchain.PaymentCommand, msg: str) -> offchain.Command:
        return cmd.new_command(status=Status.abort, abort_code=AbortCode.reject_kyc_data, abort_message=msg)

    def _ready_for_settlement(self, account_id: str, cmd: offchain.PaymentCommand) -> offchain.Command:
        if cmd.is_sender():
            return cmd.new_command(status=Status.ready_for_settlement)

        sig_msg = cmd.travel_rule_metadata_signature_message(self.diem_account.account.hrp)
        sig = self.diem_account.account.compliance_key.sign(sig_msg).hex()
        kyc_data = self.store.find(Account, id=account_id).kyc_data_object()
        return cmd.new_command(recipient_signature=sig, kyc_data=kyc_data, status=Status.ready_for_settlement)


class App(BackgroundTasks):
    def create_account(self, data: JsonInput) -> Account:
        account = self.store.create(
            Account,
            kyc_data=data.get_nullable("kyc_data", str, self._validate_kyc_data),
            # reject_additional_kyc_data_request is belongs to mini-wallet stub API, used for
            # setting up mini-wallet stub to reject additional_kyc_data request.
            reject_additional_kyc_data_request=data.get_nullable("reject_additional_kyc_data_request", bool),
        )
        balances = data.get_nullable("balances", dict)
        if balances:
            for c, a in balances.items():
                self._create_transaction(
                    account.id, Transaction.Status.completed, JsonInput({"currency": c, "amount": a})
                )
        return Account(id=account.id)

    def create_account_payment(self, account_id: str, data: JsonInput) -> Payment:
        self.store.find(Account, id=account_id)
        payee = data.get("payee", str, self._validate_account_identifier)
        txn = self._create_transaction(account_id, Transaction.Status.pending, data, payee=payee)
        return Payment(id=txn.id, account_id=account_id, payee=payee, currency=txn.currency, amount=txn.amount)

    def create_account_payment_uri(self, account_id: str, data: JsonInput) -> PaymentUri:
        currency = data.get_nullable("currency", str, self._validate_currency_code)
        amount = data.get_nullable("amount", int, self._validate_amount)
        self.store.find(Account, id=account_id)
        sub = self._gen_subaddress(account_id)
        diem_acc_id = self.diem_account.account.account_identifier(sub.subaddress_hex)
        uri = identifier.encode_intent(diem_acc_id, currency, amount)
        return PaymentUri(id=sub.id, account_id=account_id, payment_uri=uri)

    def get_account_balances(self, account_id: str) -> Dict[str, int]:
        self.store.find(Account, id=account_id)
        return self._balances(account_id)

    def get_account_events(self, account_id: str) -> List[Event]:
        return self.store.find_all(Event, account_id=account_id)

    def _create_transaction(
        self, account_id: str, status: str, data: JsonInput, payee: Optional[str] = None
    ) -> Transaction:
        return self.store.create(
            Transaction,
            account_id=account_id,
            currency=data.get("currency", str, self._validate_currency_code),
            amount=data.get("amount", int, self._validate_amount),
            payee=payee,
            status=status,
            before_create=self._validate_account_balance,
        )
