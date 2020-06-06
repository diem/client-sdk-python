# pyre-strict

from ._types import SignedTransaction, AccountKey
import typing

class TransactionUtils:
    @staticmethod
    def createSignedTransaction(
        sender_private_key: bytes,
        sender_sequence: int,
        *ignore: typing.Any,
        expiration_time: int,
        script_bytes : bytes,
        max_gas_amount: int = 1_000_000,
        gas_unit_price: int = 0,
        gas_identifier: str = "LBR"
    ) -> bytes: ...

    @staticmethod
    def createP2PTransactionScriptBytes(
        receiver: bytes,
        receiver_authkey_prefix: bytes,
        amount: int,
        metadata: bytes = b"",
        metadata_signature: bytes = b"",
        identifier: str = "LBR",
    ) -> bytes: ...

    @staticmethod
    def createAddCurrencyTransactionScriptBytes(identifier: str = "LBR") -> bytes: ...

    @staticmethod
    def parse(version: int, lcs_bytes: bytes, gas: int) -> SignedTransaction: ...

class AccountKeyUtils:
    @staticmethod
    def from_private_key(private_bytes: bytes) -> AccountKey: ...
