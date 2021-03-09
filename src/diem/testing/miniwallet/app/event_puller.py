# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import copy
from dataclasses import dataclass, field
from typing import Dict, Callable, Any
from .store import InMemoryStore, NotFoundError
from .models import Transaction, Subaddress, PaymentCommand, RefundReason
from .... import jsonrpc, diem_types, txnmetadata, identifier, utils


PENDING_INBOUND_ACCOUNT_ID: str = "pending_inbound_account"


@dataclass
class EventPuller:
    client: jsonrpc.Client
    store: InMemoryStore
    hrp: str
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
            state = copy(self.state)
            self.fetch(lambda _: None)

    def save_payment_txn(self, event: jsonrpc.Event) -> None:
        try:
            self._save_payment_txn(event)
        except (NotFoundError, ValueError) as e:
            self._create_txn(PENDING_INBOUND_ACCOUNT_ID, event)
            self.store.create_event(PENDING_INBOUND_ACCOUNT_ID, "info", str(e))

    def _save_payment_txn(self, event: jsonrpc.Event) -> None:
        metadata = txnmetadata.decode_structure(event.data.metadata)
        if isinstance(metadata, diem_types.GeneralMetadataV0):
            try:
                res = self.store.find(Subaddress, subaddress_hex=utils.hex(metadata.to_subaddress))
                return self._create_txn(res.account_id, event, subaddress_hex=res.subaddress_hex)
            except NotFoundError:
                self._create_txn(PENDING_INBOUND_ACCOUNT_ID, event)
                payee = identifier.encode_account(event.data.sender, metadata.from_subaddress, self.hrp)
                return self._refund(payee, RefundReason.invalid_subaddress, event)
        elif isinstance(metadata, diem_types.TravelRuleMetadataV0) and metadata.off_chain_reference_id:
            cmd = self.store.find(PaymentCommand, reference_id=metadata.off_chain_reference_id)
            return self._create_txn(cmd.account_id, event, reference_id=cmd.reference_id)
        elif isinstance(metadata, diem_types.RefundMetadataV0):
            version = int(metadata.transaction_version)
            reason = RefundReason.from_diem_type(metadata.reason)
            diem_txn = self.client.get_transactions(version, 1)[0]
            if diem_txn.transaction.script and diem_txn.transaction.script.metadata:
                original_metadata = txnmetadata.decode_structure(diem_txn.transaction.script.metadata)
                if isinstance(original_metadata, diem_types.GeneralMetadataV0):
                    original_sender_subaddress = utils.hex(original_metadata.from_subaddress)
                    sub = self.store.find(Subaddress, subaddress_hex=original_sender_subaddress)
                    return self._create_txn(
                        sub.account_id, event, refund_diem_txn_version=version, refund_reason=reason
                    )
        raise ValueError("unrecognized metadata: %r" % event.data.metadata)

    def _refund(self, payee: str, reason: RefundReason, event: jsonrpc.Event) -> None:
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
        self.store.create(
            Transaction,
            account_id=account_id,
            currency=event.data.amount.currency,
            amount=event.data.amount.amount,
            diem_transaction_version=event.transaction_version,
            status=Transaction.Status.completed,
            **kwargs,
        )
