# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Tuple, Optional, Union
from .models import Transaction, RefundReason
from ... import LocalAccount
from .... import jsonrpc, identifier, offchain, stdlib, utils, txnmetadata, diem_types


@dataclass
class DiemAccount:
    _account: LocalAccount
    _client: jsonrpc.Client

    @property
    def hrp(self) -> str:
        return self._account.hrp

    def sign_by_compliance_key(self, msg: bytes) -> bytes:
        return self._account.compliance_key.sign(msg)

    def account_identifier(self, subaddress: Union[str, bytes, None] = None) -> str:
        return self._account.account_identifier(subaddress)

    def decode_account_identifier(self, encoded_id: str) -> Tuple[diem_types.AccountAddress, Optional[bytes]]:
        return identifier.decode_account(encoded_id, self.hrp)

    def refund_metadata(self, version: int, reason: RefundReason) -> Tuple[bytes, bytes]:
        return (txnmetadata.refund_metadata(version, reason.to_diem_type()), b"")

    def general_metadata(self, from_subaddress: bytes, payee: str) -> Tuple[bytes, bytes]:
        to_account, to_subaddress = identifier.decode_account(payee, self.hrp)
        return (txnmetadata.general_metadata(from_subaddress, to_subaddress), b"")

    def travel_metadata(self, cmd: offchain.PaymentCommand) -> Tuple[bytes, bytes]:
        metadata = cmd.travel_rule_metadata(self.hrp)
        return (metadata, bytes.fromhex(str(cmd.payment.recipient_signature)))

    def submit_p2p(self, txn: Transaction, metadata: Tuple[bytes, bytes]) -> str:
        to_account, to_subaddress = identifier.decode_account(str(txn.payee), self.hrp)
        script = stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(txn.currency),
            amount=txn.amount,
            payee=to_account,
            metadata=metadata[0],
            metadata_signature=metadata[1],
        )
        return self._account.submit_txn(self._client, script).bcs_serialize().hex()
