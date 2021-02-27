# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import copy
from dataclasses import dataclass, field
from typing import Dict, Callable, Any
from .store import InMemoryStore
from .models import Transaction, Subaddress, PaymentCommand
from .... import jsonrpc, diem_types, txnmetadata


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
        metadata = txnmetadata.decode_structure(event.data.metadata)
        if isinstance(metadata, diem_types.GeneralMetadataV0) and metadata.to_subaddress:
            res = self.store.find(Subaddress, subaddress_hex=metadata.to_subaddress.hex())
            return self._create_txn(event, account_id=res.account_id, subaddress_hex=res.subaddress_hex)
        if isinstance(metadata, diem_types.TravelRuleMetadataV0) and metadata.off_chain_reference_id:
            cmd = self.store.find(PaymentCommand, reference_id=metadata.off_chain_reference_id)
            return self._create_txn(event, account_id=cmd.account_id, reference_id=cmd.reference_id)
        raise ValueError("unsupported metadata: %s" % metadata)

    def _create_txn(self, event: jsonrpc.Event, **kwargs: Any) -> None:
        self.store.create(
            Transaction,
            currency=event.data.amount.currency,
            amount=event.data.amount.amount,
            diem_transaction_version=event.transaction_version,
            status=Transaction.Status.completed,
            **kwargs,
        )
