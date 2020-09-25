# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import hashlib
import typing

from . import libra_types, serde_types


ACCOUNT_ADDRESS_LEN: int = 16
LIBRA_HASH_PREFIX: bytes = b"LIBRA::"
ROOT_ADDRESS: str = "0000000000000000000000000a550c18"
TREASURY_ADDRESS: str = "0000000000000000000000000b1e55ed"
CORE_CODE_ADDRESS: str = "00000000000000000000000000000001"


class InvalidAccountAddressError(Exception):
    pass


def account_address(addr: typing.Union[bytes, str]) -> libra_types.AccountAddress:
    if isinstance(addr, str):
        try:
            return account_address(bytes.fromhex(addr))
        except ValueError as e:
            raise InvalidAccountAddressError(e)

    if len(addr) != ACCOUNT_ADDRESS_LEN:
        raise InvalidAccountAddressError(
            "account address bytes length should be {ACCOUNT_ADDRESS_LEN}, but got {len(addr)}"
        )

    return libra_types.AccountAddress(value=tuple(serde_types.uint8(x) for x in addr))


def account_address_hex(addr: typing.Union[libra_types.AccountAddress, str]) -> str:
    if isinstance(addr, str):
        return account_address_hex(account_address(addr))

    return bytes(typing.cast(typing.Iterable[int], addr.value)).hex()


def public_key_bytes(public_key: Ed25519PublicKey) -> bytes:
    return public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)


def currency_code(code: str) -> libra_types.TypeTag:
    return libra_types.TypeTag__Struct(
        value=libra_types.StructTag(
            address=account_address(CORE_CODE_ADDRESS),
            module=libra_types.Identifier(code),
            name=libra_types.Identifier(code),
            type_params=[],
        )
    )


def create_signed_transaction(
    txn: libra_types.RawTransaction, public_key: bytes, signature: bytes
) -> libra_types.SignedTransaction:
    return libra_types.SignedTransaction(
        raw_txn=txn,
        authenticator=libra_types.TransactionAuthenticator__Ed25519(
            public_key=libra_types.Ed25519PublicKey(value=public_key),
            signature=libra_types.Ed25519Signature(value=signature),
        ),
    )


def raw_transaction_signing_msg(txn: libra_types.RawTransaction) -> bytes:
    return libra_hash_seed(b"RawTransaction") + txn.lcs_serialize()


def transaction_hash(txn: libra_types.SignedTransaction) -> str:
    user_txn = libra_types.Transaction__UserTransaction(value=txn)
    return hash(libra_hash_seed(b"Transaction"), user_txn.lcs_serialize()).hex()


def libra_hash_seed(typ: bytes) -> bytes:
    return hash(LIBRA_HASH_PREFIX, typ)


def hash(b1: bytes, b2: bytes) -> bytes:
    hash = hashlib.sha3_256()
    hash.update(b1)
    hash.update(b2)

    return hash.digest()
