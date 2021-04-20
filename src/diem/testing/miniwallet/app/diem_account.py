# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from random import randrange
from typing import Tuple, Optional, Union, List
from .models import Transaction, RefundReason
from ... import LocalAccount
from .... import jsonrpc, identifier, offchain, stdlib, utils, txnmetadata, diem_types


@dataclass
class DiemAccount:
    _account: LocalAccount
    _child_accounts: List[LocalAccount]
    _client: jsonrpc.Client

    @property
    def hrp(self) -> str:
        return self._account.hrp

    def sign_by_compliance_key(self, msg: bytes) -> bytes:
        return self._account.compliance_key.sign(msg)

    def account_identifier(self, subaddress: Union[str, bytes, None] = None) -> str:
        return self._get_payment_account().account_identifier(subaddress)

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

    def submit_p2p(
        self,
        txn: Transaction,
        metadata: Tuple[bytes, bytes],
        by_address: Optional[diem_types.AccountAddress] = None,
    ) -> str:
        to_account = identifier.decode_account_address(str(txn.payee), self.hrp)
        script = stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(txn.currency),
            amount=txn.amount,
            payee=to_account,
            metadata=metadata[0],
            metadata_signature=metadata[1],
        )
        return self._get_payment_account(by_address).submit_txn(self._client, script).bcs_serialize().hex()

    def _get_payment_account(self, address: Optional[diem_types.AccountAddress] = None) -> LocalAccount:
        if address is None:
            if self._child_accounts:
                return self._child_accounts[randrange(len(self._child_accounts))]
            return self._account
        for account in self._child_accounts:
            if account.account_address == address:
                return account
        raise ValueError(
            "could not find account by address: %s in child accounts: %s"
            % (address.to_hex(), list(map(lambda a: a.to_dict(), self._child_accounts)))
        )
