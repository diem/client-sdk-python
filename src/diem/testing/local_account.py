# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Provides LocalAccount class for holding local account private key.

LocalAccount provides operations we need for creating auth key, account address and signing
raw transaction.
"""

from .. import diem_types, jsonrpc, utils, stdlib, identifier, chain_ids
from ..serde_types import uint64

from ..auth_key import AuthKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass, field, replace
from copy import copy
from diem.jsonrpc import AsyncClient
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
        dic.pop("account_address", None)
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

    def create_signed_txn(
        self,
        sequence_number: int,
        payload: diem_types.TransactionPayload,
        chain_id: Optional[int] = None,
    ) -> diem_types.SignedTransaction:
        _chain_id = diem_types.ChainId.from_int(chain_id) if chain_id else chain_ids.TESTNET
        return self.sign(
            diem_types.RawTransaction(  # pyre-ignore
                sender=self.account_address,
                sequence_number=uint64(sequence_number),
                payload=payload,
                max_gas_amount=uint64(self.txn_max_gas_amount),
                gas_unit_price=uint64(self.txn_gas_unit_price),
                gas_currency_code=self.txn_gas_currency_code,
                expiration_timestamp_secs=uint64(int(time.time()) + self.txn_expire_duration_secs),
                chain_id=_chain_id,
            )
        )

    async def submit_txn(
        self, client: AsyncClient, payload: diem_types.TransactionPayload
    ) -> diem_types.SignedTransaction:
        """submit transaction with the given script

        This function creates transaction with current account sequence number (by json-rpc `get_account`
        method).
        """

        seq = await client.get_account_sequence(self.account_address)
        txn = self.create_signed_txn(seq, payload)
        await client.submit(txn)
        return txn

    async def submit_and_wait_for_txn(
        self, client: AsyncClient, payload: diem_types.TransactionPayload
    ) -> jsonrpc.Transaction:
        """Submit transaction with the payload by the account and wait for execution complete

        1. Create signed transaction for the given script function.
        2. Submit signed transaction.
        3. Wait for transaction execution finished.
        """

        txn = await self.submit_txn(client, payload)
        return await client.wait_for_transaction(txn, timeout_secs=self.txn_expire_duration_secs)

    async def rotate_dual_attestation_info(
        self, client: AsyncClient, base_url: str, compliance_key: Optional[bytes] = None
    ) -> jsonrpc.Transaction:
        if not compliance_key:
            compliance_key = self.compliance_public_key_bytes
        payload = stdlib.encode_rotate_dual_attestation_info_script_function(
            new_url=base_url.encode("utf-8"), new_key=compliance_key
        )
        return await self.submit_and_wait_for_txn(client, payload=payload)

    async def gen_child_vasp(self, client: AsyncClient, initial_balance: int, currency: str) -> "LocalAccount":
        """Generates a new ChildVASP account if `self` is a ParentVASP account.

        Raisees error with transaction execution failure if `self` is not a ParentVASP account.
        """

        child_vasp, payload = self.new_child_vasp(initial_balance, currency)
        await self.submit_and_wait_for_txn(client, payload=payload)
        return child_vasp

    def new_child_vasp(
        self, initial_balance: int, currency: str
    ) -> Tuple["LocalAccount", diem_types.TransactionPayload]:
        """Creates a new ChildVASP local account and script function"""

        child_vasp = replace(self, private_key=Ed25519PrivateKey.generate())
        payload = stdlib.encode_create_child_vasp_account_script_function(
            coin_type=utils.currency_code(currency),
            child_address=child_vasp.account_address,
            auth_key_prefix=child_vasp.auth_key.prefix(),
            add_all_currencies=False,
            child_initial_balance=initial_balance,
        )
        return (child_vasp, payload)

    def to_dict(self) -> Dict[str, str]:
        """export to a string only dictionary for saving and importing as config

        private keys will be exported as hex-encded raw key bytes.
        """

        d = copy(self.__dict__)
        d["private_key"] = utils.private_key_bytes(self.private_key).hex()
        d["compliance_key"] = utils.private_key_bytes(self.compliance_key).hex()
        d["account_address"] = self.account_address.to_hex()
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def write_to_file(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_json())

    def __str__(self) -> str:
        return self.to_json()
