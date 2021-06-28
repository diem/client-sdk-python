# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import asdict
from typing import Dict, Any
from .store import NotFoundError
from .models import Account, Subaddress, PaymentCommand, Transaction, ReferenceID
from .app import App
from .... import jsonrpc, offchain, utils
from ....offchain import (
    Status,
    AbortCode,
    CommandResponseObject,
    CommandRequestObject,
    command_error,
    ErrorCode,
    ReferenceIDCommandObject,
    ReferenceIDCommandResultObject,
    from_dict,
    to_dict,
)


class OffChainAPIv2:
    def __init__(self, app: App) -> None:
        self.app = app
        self.cache: Dict[str, CommandResponseObject] = {}

    def process(self, request_id: str, sender_address: str, request_bytes: bytes) -> CommandResponseObject:
        try:
            if not request_id:
                raise offchain.protocol_error(
                    offchain.ErrorCode.missing_http_header, "missing %s" % offchain.X_REQUEST_ID
                )
            if not offchain.UUID_REGEX.match(request_id):
                raise offchain.protocol_error(
                    offchain.ErrorCode.invalid_http_header, "invalid %s" % offchain.X_REQUEST_ID
                )
            request = self.app.offchain.deserialize_inbound_request(sender_address, request_bytes)
        except offchain.Error as e:
            err_msg = "process offchain request id or bytes is invalid, request id: %s, bytes: %s"
            self.app.logger.exception(err_msg, request_id, request_bytes)
            return offchain.reply_request(cid=None, err=e.obj)

        cached = self.cache.get(request.cid)
        if cached:
            return cached
        response = self._process_offchain_request(sender_address, request)
        self.cache[request.cid] = response
        return response

    def jws_serialize(self, resp: CommandResponseObject) -> bytes:
        return offchain.jws.serialize(resp, self.app.diem_account.sign_by_compliance_key)

    def send_dual_attestation_transaction(self, txn: Transaction) -> None:
        try:
            cmd = self.app.store.find(PaymentCommand, reference_id=txn.reference_id)
            if cmd.is_sender:
                if cmd.is_abort:
                    status = Transaction.Status.canceled
                    self.app.store.update(txn, status=status, cancel_reason="exchange kyc data abort")
                elif cmd.is_ready:
                    signed_txn = self.app.diem_account.submit_p2p(
                        txn,
                        self.app.txn_metadata(txn),
                        by_address=cmd.to_offchain_command().sender_account_address(self.app.diem_account.hrp),
                    )
                    self.app.store.update(txn, signed_transaction=signed_txn)
        except NotFoundError:
            self.send_initial_payment_command(txn)

    def send_initial_payment_command(self, txn: Transaction) -> offchain.PaymentCommand:
        account = self.app.store.find(Account, id=txn.account_id)
        command = offchain.PaymentCommand.init(
            sender_account_id=self.app.diem_account.account_identifier(txn.subaddress()),
            sender_kyc_data=account.kyc_data_object(),
            currency=txn.currency,
            amount=txn.amount,
            receiver_account_id=str(txn.payee),
            reference_id=txn.reference_id,
        )
        self._create_payment_command(txn.account_id, command)
        self.app.store.update(txn, reference_id=command.reference_id())
        self._send_offchain_command(command)
        return command

    def _process_offchain_request(self, sender_address: str, request: CommandRequestObject) -> CommandResponseObject:
        try:
            handler = "_handle_offchain_%s" % utils.to_snake(request.command_type)
            if not hasattr(self, handler):
                raise offchain.protocol_error(
                    offchain.ErrorCode.unknown_command_type,
                    "unknown command_type: %s" % request.command_type,
                    field="command_type",
                )
            result = getattr(self, handler)(sender_address, request)
            return offchain.reply_request(cid=request.cid, result=result)
        except offchain.Error as e:
            err_msg = "process offchain request failed, sender_address: %s, request: %s"
            self.app.logger.exception(err_msg, sender_address, request)
            return offchain.reply_request(cid=request.cid, err=e.obj)

    def _handle_offchain_ping_command(self, sender_address: str, request: CommandRequestObject) -> None:
        pass

    def _handle_offchain_payment_command(self, sender_address: str, request: CommandRequestObject) -> None:
        new_offchain_cmd = self.app.offchain.process_inbound_payment_command_request(sender_address, request)
        try:
            cmd = self.app.store.find(PaymentCommand, reference_id=new_offchain_cmd.reference_id())
            if new_offchain_cmd != cmd.to_offchain_command():
                self._update_payment_command(cmd, new_offchain_cmd, validate=True)
        except NotFoundError:
            subaddress = utils.hex(new_offchain_cmd.my_subaddress(self.app.diem_account.hrp))
            account_id = self.app.store.find(Subaddress, subaddress_hex=subaddress).account_id
            self._create_payment_command(account_id, new_offchain_cmd, validate=True)

    def _handle_offchain_reference_i_d_command(
        self, request_sender_address: str, request: offchain.CommandRequestObject
    ) -> Dict[str, Any]:
        ref_id_command_object = from_dict(request.command, ReferenceIDCommandObject)

        # Check if reference ID is duplicate
        try:
            self.app.validate_unique_reference_id(ref_id_command_object.reference_id)
        except ValueError:
            msg = f"Reference ID {ref_id_command_object.reference_id} already exists"
            raise command_error(ErrorCode.duplicate_reference_id, msg)
        # Check if receiver has a diem ID in this wallet
        try:
            account = self.app.store.find(Account, diem_id=ref_id_command_object.receiver)
        except NotFoundError:
            raise command_error(
                ErrorCode.invalid_receiver,
                f"Receiver with Diem ID {ref_id_command_object.receiver} not found",
                field="receiver",
            )
        self.app.store.create(
            ReferenceID,
            account_id=account.id,
            reference_id=ref_id_command_object.reference_id,
        )
        return to_dict(
            ReferenceIDCommandResultObject(
                receiver_address=self.app.diem_account.account_identifier(),
            )
        )

    def _create_payment_command(self, account_id: str, cmd: offchain.PaymentCommand, validate: bool = False) -> None:
        self.app.store.create(
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
        prior = cmd.to_offchain_command()
        self.app.store.update(
            cmd,
            before_update=lambda _: offchain_cmd.validate(prior) if validate else None,
            cid=offchain_cmd.id(),
            is_inbound=offchain_cmd.is_inbound(),
            is_abort=offchain_cmd.is_abort(),
            is_ready=offchain_cmd.is_both_ready(),
            payment_object=asdict(offchain_cmd.payment),
        )

    def _process_offchain_commands(self) -> None:
        cmds = self.app.store.find_all(
            PaymentCommand, is_inbound=True, is_abort=False, is_ready=False, process_error=None
        )
        for cmd in cmds:
            if self.app.store.find(Account, id=cmd.account_id).disable_background_tasks:
                self.app.logger.debug("account bg tasks disabled, ignore %s", cmd)
                continue
            try:
                offchain_cmd = cmd.to_offchain_command()
                action = offchain_cmd.follow_up_action()
                if action:
                    fn = getattr(self, "_offchain_action_%s" % action.value)
                    new_offchain_cmd = fn(cmd.account_id, offchain_cmd)
                    self._update_payment_command(cmd, new_offchain_cmd)
                    self._send_offchain_command(new_offchain_cmd)
            except Exception as e:
                self.app.logger.exception(e)
                self.app.store.update(cmd, process_error=str(e))

    def _send_offchain_command(self, command: offchain.Command) -> CommandResponseObject:
        """send offchain command with retries

        We only do limited in process retries, as we are expecting counterparty service
        should be available in dev / testing environment, and fail immediately if counterparty
        service is not available.
        In production environment, you may need implement better retry system for handling
        counterparty service temporarily not available case.
        """

        retry = jsonrpc.Retry(5, 0.2, Exception)
        return retry.execute(lambda: self.send_offchain_command_without_retries(command))

    def send_offchain_command_without_retries(self, command: offchain.Command) -> CommandResponseObject:
        return self.app.offchain.send_command(command, self.app.diem_account.sign_by_compliance_key)

    def _offchain_action_evaluate_kyc_data(self, account_id: str, cmd: offchain.PaymentCommand) -> offchain.Command:
        op_kyc_data = cmd.counterparty_actor_obj().kyc_data
        if op_kyc_data is None or self.app.kyc_sample.match_kyc_data("reject", op_kyc_data):
            return self._new_reject_kyc_data(cmd, "KYC data is rejected")
        elif self.app.kyc_sample.match_any_kyc_data(["soft_match", "soft_reject"], op_kyc_data):
            return cmd.new_command(status=Status.soft_match)
        elif self.app.kyc_sample.match_kyc_data("minimum", op_kyc_data):
            return self._ready_for_settlement(account_id, cmd)
        else:
            return self._new_reject_kyc_data(cmd, "KYC data is not from samples")

    def _offchain_action_clear_soft_match(self, account_id: str, cmd: offchain.PaymentCommand) -> offchain.Command:
        account = self.app.store.find(Account, id=account_id)
        if account.reject_additional_kyc_data_request:
            return self._new_reject_kyc_data(cmd, "no need additional KYC data")
        return cmd.new_command(additional_kyc_data="{%r: %r}" % ("account_id", account_id))

    def _offchain_action_review_kyc_data(self, account_id: str, cmd: offchain.PaymentCommand) -> offchain.Command:
        op_kyc_data = cmd.counterparty_actor_obj().kyc_data
        if op_kyc_data is None or self.app.kyc_sample.match_kyc_data("soft_reject", op_kyc_data):
            return self._new_reject_kyc_data(cmd, "KYC data review result is reject")
        return self._ready_for_settlement(account_id, cmd)

    def _new_reject_kyc_data(self, cmd: offchain.PaymentCommand, msg: str) -> offchain.Command:
        return cmd.new_command(status=Status.abort, abort_code=AbortCode.reject_kyc_data, abort_message=msg)

    def _ready_for_settlement(self, account_id: str, cmd: offchain.PaymentCommand) -> offchain.Command:
        if cmd.is_sender():
            return cmd.new_command(status=Status.ready_for_settlement)

        sig_msg = cmd.travel_rule_metadata_signature_message(self.app.diem_account.hrp)
        sig = self.app.diem_account.sign_by_compliance_key(sig_msg).hex()
        kyc_data = self.app.store.find(Account, id=account_id).kyc_data_object()
        return cmd.new_command(recipient_signature=sig, kyc_data=kyc_data, status=Status.ready_for_settlement)
