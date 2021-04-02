# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Provides LocalAccount class for holding local account private key.

LocalAccount provides operations we need for creating auth key, account address and signing
raw transaction.
"""

from .. import diem_types, jsonrpc, utils, stdlib, identifier
from ..serde_types import uint64

from ..auth_key import AuthKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
from copy import copy
import time, json


@dataclass
class LocalAccount:
    """LocalAccount is like a wallet account

    Some default values are initialized for testnet.

    WARN: This is handy class for creating tests for your application, but may not ideal for your
    production code, because it uses a specific implementaion of ed25519 and requires loading your
    private key into memory and hand over to code from external.
    You should always choose more secure way to handle your private key
    (e.g. https://en.wikipedia.org/wiki/Hardware_security_module) in production and do not give
    your private key to any code from external if possible.
    """

    @staticmethod
    def generate() -> "LocalAccount":
        """Generate a random private key and initialize local account"""

        return LocalAccount()

    @staticmethod
    def from_private_key_hex(key: str) -> "LocalAccount":
        return LocalAccount.from_dict({"private_key": key})

    @staticmethod
    def from_dict(dic: Dict[str, str]) -> "LocalAccount":
        """from a dict that is created by LocalAccount#to_dict

        The private_key and compliance_key values are hex-encoded bytes; they will
        be loaded by `Ed25519PrivateKey.from_private_bytes`.
        """

        dic = copy(dic)
        for name in ["private_key", "compliance_key"]:
            if name not in dic:
                continue
            key = dic[name]
            dic[name] = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(key))
        return LocalAccount(**dic)  # pyre-ignore

    private_key: Ed25519PrivateKey = field(default_factory=Ed25519PrivateKey.generate)
    compliance_key: Ed25519PrivateKey = field(default_factory=Ed25519PrivateKey.generate)

    hrp: str = field(default=identifier.TDM)
    txn_gas_currency_code: str = field(default="XDX")
    txn_max_gas_amount: int = field(default=1_000_000)
    txn_gas_unit_price: int = field(default=0)
    txn_expire_duration_secs: int = field(default=30)

    @property
    def auth_key(self) -> AuthKey:
        return AuthKey.from_public_key(self.public_key)

    @property
    def account_address(self) -> diem_types.AccountAddress:
        return self.auth_key.account_address()

    @property
    def public_key_bytes(self) -> bytes:
        return utils.public_key_bytes(self.public_key)

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self.private_key.public_key()

    @property
    def compliance_public_key_bytes(self) -> bytes:
        return utils.public_key_bytes(self.compliance_key.public_key())

    def account_identifier(self, subaddress: Union[str, bytes, None] = None) -> str:
        return identifier.encode_account(self.account_address, subaddress, self.hrp)

    def decode_account_identifier(self, encoded_id: str) -> Tuple[diem_types.AccountAddress, Optional[bytes]]:
        return identifier.decode_account(encoded_id, self.hrp)

    def sign(self, txn: diem_types.RawTransaction) -> diem_types.SignedTransaction:
        """Create signed transaction for given raw transaction"""

        signature = self.private_key.sign(utils.raw_transaction_signing_msg(txn))
        return utils.create_signed_transaction(txn, self.public_key_bytes, signature)

    def create_txn(self, client: jsonrpc.Client, script: diem_types.Script) -> diem_types.SignedTransaction:
        sequence_number = client.get_account_sequence(self.account_address)
        chain_id = client.get_last_known_state().chain_id
        return self.sign(
            diem_types.RawTransaction(  # pyre-ignore
                sender=self.account_address,
                sequence_number=uint64(sequence_number),
                payload=diem_types.TransactionPayload__Script(value=script),
                max_gas_amount=uint64(self.txn_max_gas_amount),
                gas_unit_price=uint64(self.txn_gas_unit_price),
                gas_currency_code=self.txn_gas_currency_code,
                expiration_timestamp_secs=uint64(int(time.time()) + self.txn_expire_duration_secs),
                chain_id=diem_types.ChainId.from_int(chain_id),
            )
        )

    def submit_txn(self, client: jsonrpc.Client, script: diem_types.Script) -> diem_types.SignedTransaction:
        """submit transaction with the given script

        This function creates transaction with current account sequence number (by json-rpc `get_account`
        method), and retries on JsonRpcError in case there is another process is submitting transaction
        at same time, which may cause SEQUENCE_NUMBER_TOO_OLD JsonRpcError.
        """
        retry = jsonrpc.Retry(10, 0.1, jsonrpc.JsonRpcError)
        return retry.execute(lambda: self._submit_txn_without_retry(client, script))

    def _submit_txn_without_retry(
        self, client: jsonrpc.Client, script: diem_types.Script
    ) -> diem_types.SignedTransaction:
        txn = self.create_txn(client, script)
        client.submit(txn)
        return txn

    def submit_and_wait_for_txn(self, client: jsonrpc.Client, script: diem_types.Script) -> jsonrpc.Transaction:
        txn = self.submit_txn(client, script)
        return client.wait_for_transaction(txn, timeout_secs=self.txn_expire_duration_secs)

    def rotate_dual_attestation_info(self, client: jsonrpc.Client, base_url: str) -> jsonrpc.Transaction:
        return self.submit_and_wait_for_txn(
            client,
            stdlib.encode_rotate_dual_attestation_info_script(
                new_url=base_url.encode("utf-8"), new_key=self.compliance_public_key_bytes
            ),
        )

    def to_dict(self) -> Dict[str, str]:
        """export to a string only dictionary for saving and importing as config

        private keys will be exported as hex-encded raw key bytes.
        """

        d = copy(self.__dict__)
        d["private_key"] = utils.private_key_bytes(self.private_key).hex()
        d["compliance_key"] = utils.private_key_bytes(self.compliance_key).hex()
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def write_to_file(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_json())
