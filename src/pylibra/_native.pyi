# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

# pyre-strict

import typing

from ._types import AccountKey, SignedTransaction

class TransactionUtils:
    @staticmethod
    def createSignedP2PTransaction(
        sender_private_key: bytes,
        receiver: bytes,
        sender_sequence: int,
        amount: int,
        *ignore: typing.Any,
        expiration_time: int,  # unix timestamp at which the tx will expire
        chain_id: int,
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
        chain_id: int,
        max_gas_amount: int = 1_000_000,
        gas_unit_price: int = 0,
        identifier: str = "LBR",
        gas_identifier: str = "LBR",
    ) -> bytes: ...
    @staticmethod
    def createSignedRotateDualAttestationInfoTransaction(
        new_url: str,
        new_key: bytes,
        *ignore: typing.Any,
        sender_private_key: bytes,
        sender_sequence: int,
        expiration_time: int,
        chain_id: int,
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
