# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Utilities for data type converting, construction and hashing."""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import hashlib
import typing

from . import libra_types, serde_types, jsonrpc, stdlib


ACCOUNT_ADDRESS_LEN: int = libra_types.AccountAddress.LENGTH
SUB_ADDRESS_LEN: int = 8
LIBRA_HASH_PREFIX: bytes = b"LIBRA::"
ROOT_ADDRESS: str = "0000000000000000000000000a550c18"
TREASURY_ADDRESS: str = "0000000000000000000000000b1e55ed"
CORE_CODE_ADDRESS: str = "00000000000000000000000000000001"


class InvalidAccountAddressError(Exception):
    pass


class InvalidSubAddressError(Exception):
    pass


def account_address(addr: typing.Union[libra_types.AccountAddress, bytes, str]) -> libra_types.AccountAddress:
    """convert an account address from hex-encoded or bytes into `libra_types.AccountAddress`

    Returns given address if it is `libra_types.AccountAddress` already
    """

    if isinstance(addr, libra_types.AccountAddress):
        return addr

    try:
        if isinstance(addr, str):
            return libra_types.AccountAddress.from_hex(addr)
        return libra_types.AccountAddress.from_bytes(addr)
    except ValueError as e:
        raise InvalidAccountAddressError(e)


def account_address_hex(addr: typing.Union[libra_types.AccountAddress, str]) -> str:
    """convert `libra_types.AccountAddress` into hex-encoded string

    This function converts given parameter into account address bytes first, then convert bytes
    into hex-encoded string
    """

    return account_address_bytes(addr).hex()


def account_address_bytes(addr: typing.Union[libra_types.AccountAddress, str]) -> bytes:
    """convert `libra_types.AccountAddress` or hex-encoded account address into bytes"""

    if isinstance(addr, str):
        return account_address_bytes(account_address(addr))

    return addr.to_bytes()


def sub_address(addr: typing.Union[str, bytes]) -> bytes:
    """convert hex-encoded sub-address into bytes

    This function validates bytes length, and raises `InvalidSubAddressError` if length
    does not match sub-address length (8 bytes)
    """

    ret = bytes.fromhex(addr) if isinstance(addr, str) else addr
    if len(ret) != SUB_ADDRESS_LEN:
        raise InvalidSubAddressError(
            f"{addr}(len={len(ret)}) is a valid sub-address, sub-address is {SUB_ADDRESS_LEN} bytes"
        )
    return ret


def public_key_bytes(public_key: Ed25519PublicKey) -> bytes:
    """convert cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey into bytes"""

    return public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)


def currency_code(code: str) -> libra_types.TypeTag:
    """converts currency code string to libra_types.TypeTag"""

    return libra_types.TypeTag.from_currency_code(code)


def type_tag_to_str(code: libra_types.TypeTag) -> str:
    """converts currency code TypeTag into string"""

    if isinstance(code, libra_types.TypeTag__Struct):
        return code.to_currency_code()

    raise TypeError(f"unknown currency code type: {code}")


def create_signed_transaction(
    txn: libra_types.RawTransaction, public_key: bytes, signature: bytes
) -> libra_types.SignedTransaction:
    """create single signed `libra_types.SignedTransaction`"""

    return libra_types.SignedTransaction.from_raw_txn_and_ed25519_key(txn, public_key, signature)


def raw_transaction_signing_msg(txn: libra_types.RawTransaction) -> bytes:
    """create signing message from given `libra_types.RawTransaction`"""

    return libra_hash_seed(b"RawTransaction") + txn.lcs_serialize()


def transaction_hash(txn: libra_types.SignedTransaction) -> str:
    """create transaction hash from given `libra_types.SignedTransaction`

    This hash string matches jsonrpc.Transaction#hash returned from Libra JSON-RPC API.
    """

    user_txn = libra_types.Transaction__UserTransaction(value=txn)
    return hash(libra_hash_seed(b"Transaction"), user_txn.lcs_serialize()).hex()


def libra_hash_seed(typ: bytes) -> bytes:
    return hash(LIBRA_HASH_PREFIX, typ)


def hash(b1: bytes, b2: bytes) -> bytes:
    hash = hashlib.sha3_256()
    hash.update(b1)
    hash.update(b2)

    return hash.digest()


def decode_transaction_script(
    txn: typing.Union[str, jsonrpc.TransactionData, jsonrpc.Transaction]
) -> stdlib.ScriptCall:
    """decode jsonrpc.Transaction#transaction#script_bytes

    Returns `stdlib.ScriptCall`, which is same object we created for `libra_types.RawTransaction`
    payload.
    You can find out script type by checking it's class name: `type(script_call).__name__`.
    See libra.stdlib documentation for more details.
    """

    if isinstance(txn, str):
        script = libra_types.Script.lcs_deserialize(bytes.fromhex(txn))
        return stdlib.decode_script(script)
    if isinstance(txn, jsonrpc.Transaction):
        return decode_transaction_script(txn.transaction.script_bytes)
    if isinstance(txn, jsonrpc.TransactionData):
        return decode_transaction_script(txn.script_bytes)

    raise TypeError(f"unknown transaction type: {txn}")
