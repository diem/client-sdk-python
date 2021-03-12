# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Utilities for data type converting, construction and hashing."""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
import hashlib
import typing, time, socket

from . import diem_types, jsonrpc, stdlib


ACCOUNT_ADDRESS_LEN: int = diem_types.AccountAddress.LENGTH
SUB_ADDRESS_LEN: int = 8
DIEM_HASH_PREFIX: bytes = b"DIEM::"
ROOT_ADDRESS: str = "0000000000000000000000000a550c18"
TREASURY_ADDRESS: str = "0000000000000000000000000b1e55ed"
CORE_CODE_ADDRESS: str = "00000000000000000000000000000001"


class InvalidAccountAddressError(Exception):
    pass


class InvalidSubAddressError(Exception):
    pass


def account_address(addr: typing.Union[diem_types.AccountAddress, bytes, str]) -> diem_types.AccountAddress:
    """convert an account address from hex-encoded or bytes into `diem_types.AccountAddress`

    Returns given address if it is `diem_types.AccountAddress` already
    """

    if isinstance(addr, diem_types.AccountAddress):
        return addr

    try:
        if isinstance(addr, str):
            return diem_types.AccountAddress.from_hex(addr)
        return diem_types.AccountAddress.from_bytes(addr)
    except ValueError as e:
        raise InvalidAccountAddressError(e)


def account_address_hex(addr: typing.Union[diem_types.AccountAddress, str]) -> str:
    """convert `diem_types.AccountAddress` into hex-encoded string

    This function converts given parameter into account address bytes first, then convert bytes
    into hex-encoded string
    """

    return account_address_bytes(addr).hex()


def account_address_bytes(addr: typing.Union[diem_types.AccountAddress, str]) -> bytes:
    """convert `diem_types.AccountAddress` or hex-encoded account address into bytes"""

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


def hex(b: typing.Optional[bytes]) -> str:
    """convert an optional bytes into hex-encoded str, returns "" if bytes is None"""

    return b.hex() if b else ""


def public_key_bytes(public_key: Ed25519PublicKey) -> bytes:
    """convert cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey into raw bytes"""

    return public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)


def private_key_bytes(private_key: Ed25519PrivateKey) -> bytes:
    """convert cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey into raw bytes"""

    return private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )


def currency_code(code: str) -> diem_types.TypeTag:
    """converts currency code string to diem_types.TypeTag"""

    return diem_types.TypeTag.from_currency_code(code)


def type_tag_to_str(code: diem_types.TypeTag) -> str:
    """converts currency code TypeTag into string"""

    if isinstance(code, diem_types.TypeTag__Struct):
        return code.to_currency_code()

    raise TypeError(f"unknown currency code type: {code}")


def create_signed_transaction(
    txn: diem_types.RawTransaction, public_key: bytes, signature: bytes
) -> diem_types.SignedTransaction:
    """create single signed `diem_types.SignedTransaction`"""

    return diem_types.SignedTransaction.from_raw_txn_and_ed25519_key(txn, public_key, signature)


def raw_transaction_signing_msg(txn: diem_types.RawTransaction) -> bytes:
    """create signing message from given `diem_types.RawTransaction`"""

    return diem_hash_seed(b"RawTransaction") + txn.bcs_serialize()


def transaction_hash(txn: diem_types.SignedTransaction) -> str:
    """create transaction hash from given `diem_types.SignedTransaction`

    This hash string matches jsonrpc.Transaction#hash returned from Diem JSON-RPC API.
    """

    user_txn = diem_types.Transaction__UserTransaction(value=txn)
    return hash(diem_hash_seed(b"Transaction"), user_txn.bcs_serialize()).hex()


def diem_hash_seed(typ: bytes) -> bytes:
    return hash(DIEM_HASH_PREFIX, typ)


def hash(b1: bytes, b2: bytes) -> bytes:
    hash = hashlib.sha3_256()
    hash.update(b1)
    hash.update(b2)

    return hash.digest()


def decode_transaction_script(
    txn: typing.Union[str, jsonrpc.TransactionData, jsonrpc.Transaction]
) -> stdlib.ScriptCall:
    """decode jsonrpc.Transaction#transaction#script_bytes

    Returns `stdlib.ScriptCall`, which is same object we created for `diem_types.RawTransaction`
    payload.
    You can find out script type by checking it's class name: `type(script_call).__name__`.
    See diem.stdlib documentation for more details.
    """

    if isinstance(txn, str):
        script = diem_types.Script.bcs_deserialize(bytes.fromhex(txn))
        return stdlib.decode_script(script)
    if isinstance(txn, jsonrpc.Transaction):
        return decode_transaction_script(txn.transaction.script_bytes)
    if isinstance(txn, jsonrpc.TransactionData):
        return decode_transaction_script(txn.script_bytes)

    raise TypeError(f"unknown transaction type: {txn}")


def balance(account: jsonrpc.Account, currency: str) -> int:
    for b in account.balances:
        if b.currency == currency:
            return b.amount
    return 0


def to_snake(o: typing.Any) -> str:  # pyre-ignore
    if isinstance(o, str):
        return "".join(["_" + i.lower() if i.isupper() else i for i in o]).lstrip("_")
    elif hasattr(o, "__name__"):
        return to_snake(getattr(o, "__name__"))
    return to_snake(type(o))


def wait_for_port(port: int, host: str = "localhost", timeout: float = 5.0) -> None:
    """Wait for a port ready for accepting TCP connections.
    Args:
        port (int): port number.
        host (str): host address on which the port should exist.
        timeout (float): in seconds. wait timeout
    Raises:
        TimeoutError
    """

    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as e:
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError("waited %s for %s:%s accept connection." % (timeout, host, port)) from e
            time.sleep(0.01)
