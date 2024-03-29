# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import Dict, Any, AsyncIterator
from diem import jsonrpc, diem_types, txnmetadata, identifier, utils
from diem.jsonrpc import AsyncClient
from .store import InMemoryStore, NotFoundError
from .pending_account import PENDING_INBOUND_ACCOUNT_ID
from .models import Transaction, Subaddress, PaymentCommand, RefundReason, Account, ReferenceID
import copy, logging
import uuid


@dataclass
class EventPuller:
    client: AsyncClient
    store: InMemoryStore
    hrp: str
    logger: logging.Logger
    state: Dict[str, int] = field(default_factory=dict)

    async def add_received_events_key(self, address: diem_types.AccountAddress) -> None:
        account = await self.client.must_get_account(address)
        self.state[account.received_events_key] = 0

    async def process(self) -> None:
        async for event in self.pull_events():
            if event.data.type == jsonrpc.EVENT_DATA_RECEIVED_PAYMENT:
                await self.save_payment_txn(event)

    async def head(self) -> None:
        state = None
        while state != self.state:
            state = copy.copy(self.state)
            async for event in self.pull_events():
                pass

    async def pull_events(self, batch_size: int = 100) -> AsyncIterator[jsonrpc.Event]:
        for key, seq in self.state.items():
            events = await self.client.get_events(key, seq, batch_size)
            if events:
                for event in events:
                    yield (event)
                    self.state[key] = event.sequence_number + 1

    async def save_payment_txn(self, event: jsonrpc.Event) -> None:
        self.logger.info("processing Event:\n%s", event)
        try:
            await self._save_payment_txn(event)
        except (NotFoundError, ValueError):
            self.logger.exception("process event failed")
            self._create_txn(PENDING_INBOUND_ACCOUNT_ID, event)

    async def _save_payment_txn(self, event: jsonrpc.Event) -> None:  # noqa: C901
        metadata = txnmetadata.decode_structure(event.data.metadata)
        if isinstance(metadata, diem_types.GeneralMetadataV0):
            subaddress = utils.hex(metadata.to_subaddress)
            try:
                res = self.store.find(Subaddress, subaddress_hex=subaddress)
            except NotFoundError:
                self.logger.exception("invalid general metadata to_subaddress")
                return await self._refund(RefundReason.invalid_subaddress, event)
            return self._create_txn(res.account_id, event, subaddress_hex=res.subaddress_hex)
        elif isinstance(metadata, diem_types.TravelRuleMetadataV0):
            try:
                cmd = self.store.find(PaymentCommand, reference_id=metadata.off_chain_reference_id)
            except NotFoundError:
                self.logger.exception("invalid travel rule metadata off-chain reference id")
                return await self._refund(RefundReason.other, event)
            return self._create_txn(cmd.account_id, event, reference_id=cmd.reference_id)
        elif isinstance(metadata, diem_types.RefundMetadataV0):
            version = int(metadata.transaction_version)
            reason = RefundReason.from_diem_type(metadata.reason)
            account_id = await self._find_refund_account_id(version)
            self._create_txn(account_id, event, refund_diem_txn_version=version, refund_reason=reason)
        elif isinstance(metadata, diem_types.PaymentMetadataV0):
            reference_id = str(uuid.UUID(bytes=metadata.to_bytes()))
            try:
                ref_id = self.store.find(ReferenceID, reference_id=reference_id)
            except NotFoundError:
                self.logger.exception("Transaction with reference ID %r not found" % reference_id)
                return await self._refund(RefundReason.other, event)
            return self._create_txn(ref_id.account_id, event, reference_id=reference_id)
        else:
            raise ValueError("unrecognized metadata: %r" % event.data.metadata)

    async def _find_refund_account_id(self, version: int) -> str:
        diem_txns = await self.client.get_transactions(version, 1, include_events=True)
        if diem_txns:
            diem_txn = diem_txns[0]
            self.logger.error("diem_txn script: %r", diem_txn.transaction.script)
            event = diem_txn.events[0]
            original_metadata = txnmetadata.decode_structure(event.data.metadata)
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

    async def _refund(self, reason: RefundReason, event: jsonrpc.Event) -> None:
        self._create_txn(PENDING_INBOUND_ACCOUNT_ID, event)
        payee = identifier.encode_account(event.data.sender, None, self.hrp)
        self.store.create(
            Transaction,
            account_id=PENDING_INBOUND_ACCOUNT_ID,
            status=Transaction.Status.pending,
            type=Transaction.Type.sent_payment,
            currency=event.data.amount.currency,
            amount=event.data.amount.amount,
            payee=payee,
            payee_account_identifier=payee,
            refund_diem_txn_version=event.transaction_version,
            refund_reason=reason,
        )

    def _create_txn(self, account_id: str, event: jsonrpc.Event, **kwargs: Any) -> None:
        if self.store.find(Account, id=account_id).disable_background_tasks:
            self.logger.debug("account(%s) bg tasks disabled, ignore %s", account_id, event)
            return

        self.logger.info("account(id=%s) receives payment amount %s", account_id, event.data.amount.amount)
        self.store.create(
            Transaction,
            account_id=account_id,
            currency=event.data.amount.currency,
            amount=event.data.amount.amount,
            diem_transaction_version=event.transaction_version,
            status=Transaction.Status.completed,
            type=Transaction.Type.received_payment,
            **kwargs,
        )
