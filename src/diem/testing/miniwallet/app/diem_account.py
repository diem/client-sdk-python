# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Tuple
from .models import Transaction, RefundReason
from ... import LocalAccount
from .... import jsonrpc, identifier, offchain, stdlib, utils, txnmetadata


@dataclass
class DiemAccount:
    account: LocalAccount
    client: jsonrpc.Client

    def refund_metadata(self, version: int, reason: RefundReason) -> Tuple[bytes, bytes]:
        return (txnmetadata.refund_metadata(version, reason.to_diem_type()), b"")

    def general_metadata(self, from_subaddress: bytes, payee: str) -> Tuple[bytes, bytes]:
        to_account, to_subaddress = identifier.decode_account(payee, self.account.hrp)
        return (txnmetadata.general_metadata(from_subaddress, to_subaddress), b"")

    def travel_metadata(self, cmd: offchain.PaymentCommand) -> Tuple[bytes, bytes]:
        metadata = cmd.travel_rule_metadata(self.account.hrp)
        return (metadata, bytes.fromhex(str(cmd.payment.recipient_signature)))

    def submit_p2p(self, txn: Transaction, metadata: Tuple[bytes, bytes]) -> str:
        to_account, to_subaddress = identifier.decode_account(str(txn.payee), self.account.hrp)
        script = stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(txn.currency),
            amount=txn.amount,
            payee=to_account,
            metadata=metadata[0],
            metadata_signature=metadata[1],
        )
        return self.account.submit_txn(self.client, script).bcs_serialize().hex()
