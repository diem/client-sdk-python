# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import Dict, Callable, Any
from .store import InMemoryStore, NotFoundError
from .models import Transaction, Subaddress, PaymentCommand, RefundReason
from .... import jsonrpc, diem_types, txnmetadata, identifier, utils
import copy, logging


PENDING_INBOUND_ACCOUNT_ID: str = "pending_inbound_account"


@dataclass
class EventPuller:
    client: jsonrpc.Client
    store: InMemoryStore
    hrp: str
    logger: logging.Logger
    state: Dict[str, int] = field(default_factory=dict)

    def add(self, address: diem_types.AccountAddress) -> None:
        account = self.client.must_get_account(address)
        self.state[account.received_events_key] = 0

    def fetch(self, process: Callable[[jsonrpc.Event], None], batch_size: int = 100) -> None:
        for key, seq in self.state.items():
            events = self.client.get_events(key, seq, batch_size)
            if events:
                for event in events:
                    process(event)
                    self.state[key] = event.sequence_number + 1

    def head(self) -> None:
        state = None
        while state != self.state:
            state = copy.copy(self.state)
            self.fetch(lambda _: None)

    def save_payment_txn(self, event: jsonrpc.Event) -> None:
        self.logger.info("processing Event:\n%s", event)
        try:
            self._save_payment_txn(event)
        except (NotFoundError, ValueError):
            self.logger.exception("process event failed")
            self._create_txn(PENDING_INBOUND_ACCOUNT_ID, event)

    def _save_payment_txn(self, event: jsonrpc.Event) -> None:
        metadata = txnmetadata.decode_structure(event.data.metadata)
        if isinstance(metadata, diem_types.GeneralMetadataV0):
            subaddress = utils.hex(metadata.to_subaddress)
            try:
                res = self.store.find(Subaddress, subaddress_hex=subaddress)
            except NotFoundError:
                self.logger.exception("invalid general metadata to_subaddress")
                return self._refund(RefundReason.invalid_subaddress, event)
            return self._create_txn(res.account_id, event, subaddress_hex=res.subaddress_hex)
        elif isinstance(metadata, diem_types.TravelRuleMetadataV0):
            try:
                cmd = self.store.find(PaymentCommand, reference_id=metadata.off_chain_reference_id)
            except NotFoundError:
                self.logger.exception("invalid travel rule metadata off-chain reference id")
                return self._refund(RefundReason.other, event)
            return self._create_txn(cmd.account_id, event, reference_id=cmd.reference_id)
        elif isinstance(metadata, diem_types.RefundMetadataV0):
            version = int(metadata.transaction_version)
            reason = RefundReason.from_diem_type(metadata.reason)
            account_id = self._find_refund_account_id(version)
            return self._create_txn(account_id, event, refund_diem_txn_version=version, refund_reason=reason)
        raise ValueError("unrecognized metadata: %r" % event.data.metadata)

    def _find_refund_account_id(self, version: int) -> str:
        diem_txns = self.client.get_transactions(version, 1)
        if diem_txns:
            diem_txn = diem_txns[0]
            self.logger.error("diem_txn script: %r", diem_txn.transaction.script)
            original_metadata = txnmetadata.decode_structure(diem_txn.transaction.script.metadata)
            if isinstance(original_metadata, diem_types.GeneralMetadataV0):
                original_sender = utils.hex(original_metadata.from_subaddress)
                try:
                    return self.store.find(Subaddress, subaddress_hex=original_sender).account_id
                except NotFoundError:
                    self.logger.exception("invalid original transaction metadata from_subaddress")
            else:
                self.logger.error("invalid original txn metadata %r", diem_txn.transaction.script.metadata)
        else:
            self.logger.error("could not find diem txn by version: %s", version)
        return PENDING_INBOUND_ACCOUNT_ID

    def _refund(self, reason: RefundReason, event: jsonrpc.Event) -> None:
        self._create_txn(PENDING_INBOUND_ACCOUNT_ID, event)
        payee = identifier.encode_account(event.data.sender, None, self.hrp)
        self.store.create(
            Transaction,
            account_id=PENDING_INBOUND_ACCOUNT_ID,
            status=Transaction.Status.pending,
            currency=event.data.amount.currency,
            amount=event.data.amount.amount,
            payee=payee,
            refund_diem_txn_version=event.transaction_version,
            refund_reason=reason,
        )

    def _create_txn(self, account_id: str, event: jsonrpc.Event, **kwargs: Any) -> None:
        self.logger.info("account(id=%s) receives payment amount %s", account_id, event.data.amount.amount)
        self.store.create(
            Transaction,
            account_id=account_id,
            currency=event.data.amount.currency,
            amount=event.data.amount.amount,
            diem_transaction_version=event.transaction_version,
            status=Transaction.Status.completed,
            **kwargs,
        )
