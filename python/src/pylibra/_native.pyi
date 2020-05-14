# pyre-strict

from ._types import SignedTransaction, AccountKey
import typing

class TransactionUtils:
    @staticmethod
    def createSignedP2PTransaction(
        sender_private_key: bytes,
        receiver: bytes,
        receiver_authkey_prefix: bytes,
        sender_sequence: int,
        num_coins_microlibra: int,
        *ignore: typing.Any,
        expiration_time: int,
        max_gas_amount: int = 1_000_000,
        gas_unit_price: int = 0,
        metadata: bytes = b"",
        metadata_signature: bytes = b"",
    ) -> bytes: ...
    @staticmethod
    def parse(version: int, lcs_bytes: bytes, gas: int) -> SignedTransaction: ...

class AccountKeyUtils:
    @staticmethod
    def from_private_key(private_bytes: bytes) -> AccountKey: ...
