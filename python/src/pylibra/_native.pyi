# pyre-strict

from ._types import SignedTransaction, AccountKey
import typing

def _createSignedTransaction(
    sender_private_key: bytes,
    sender_sequence: int,
    script_bytes: bytes,
    expiration_time: int,  # unix timestamp at which the tx will expire
    max_gas_amount: int = 1_000_000,
    gas_unit_price: int = 0,
    gas_identifier: str = "LBR",
) -> bytes: ...

class TransactionUtils:
    @staticmethod
    def createSignedP2PTransaction(
        sender_private_key: bytes,
        receiver: bytes,
        receiver_authkey_prefix: bytes,
        sender_sequence: int,
        amount: int,
        *ignore: typing.Any,
        expiration_time: int,  # unix timestamp at which the tx will expire
        max_gas_amount: int = 1_000_000,
        gas_unit_price: int = 0,
        metadata: bytes = b"",
        metadata_signature: bytes = b"",
        identifier: str = "LBR",
        gas_identifier: str = "LBR",
    ) -> bytes: ...
    @staticmethod
    def createSignedAddCurrencyTransaction(
        sender_private_key: bytes,
        sender_sequence: int,
        *ignore: typing.Any,
        expiration_time: int,  # unix timestamp at which the tx will expire
        max_gas_amount: int = 1_000_000,
        gas_unit_price: int = 0,
        identifier: str = "LBR",
        gas_identifier: str = "LBR",
    ) -> bytes: ...
    @staticmethod
    def parse(version: int, lcs_bytes: bytes, gas: int) -> SignedTransaction: ...

class AccountKeyUtils:
    @staticmethod
    def from_private_key(private_bytes: bytes) -> AccountKey: ...
