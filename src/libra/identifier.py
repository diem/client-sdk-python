# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""LIP-5 Libra Account Identifier and Intent Identifier Utilities.

See https://lip.libra.org/lip-5 for more details
"""


import typing
from urllib import parse
from typing import List

from . import libra_types, utils

LBR = "lbr"  # lbr for mainnet
TLB = "tlb"  # tlb for testnet
LIBRA_SUBADDRESS_SIZE = 8  # in bytes (for V1)
LIBRA_ZERO_SUBADDRESS: bytes = b"\0" * LIBRA_SUBADDRESS_SIZE

# Bech32 constants
_BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_SEPARATOR = "1"
_BECH32_CHECKSUM_CHAR_SIZE = 6

# LIBRA constants
_LIBRA_HRP: List[str] = [LBR, TLB]
_LIBRA_ADDRESS_SIZE = 16  # in bytes
_LIBRA_BECH32_VERSION = 1
_LIBRA_BECH32_SIZE = 50  # in characters


class InvalidIntentIdentifierError(Exception):
    pass


class Intent:
    """Intent is a struct hold data decoded from Libra Intent Identifier string"""

    account_address: libra_types.AccountAddress
    sub_address: typing.Optional[bytes]
    currency_code: str
    amount: int

    def __init__(
        self,
        account_address: libra_types.AccountAddress,
        sub_address: typing.Optional[bytes],
        currency_code: str,
        amount: int,
    ) -> None:
        self.account_address = account_address
        self.sub_address = sub_address
        self.currency_code = currency_code
        self.amount = amount

    @property
    def account_address_bytes(self) -> bytes:
        return self.account_address.to_bytes()


def encode_intent(encoded_account_identifier: str, currency_code: str, amount: int) -> str:
    """
    Encode account identifier string(encoded), currency code and amount into
    Libra intent identifier (https://lip.libra.org/lip-5/)
    """

    return "libra://%s?c=%s&am=%d" % (encoded_account_identifier, currency_code, amount)


def decode_intent(encoded_intent_identifier: str, hrp: str) -> Intent:
    """
    Decode Libra intent identifier (https://lip.libra.org/lip-5/) int 3 parts:
    1. account identifier: account address & sub-address
    2. currency code
    3. amount

    InvalidIntentIdentifierError is raised if given identifier is invalid
    """

    result = parse.urlparse(encoded_intent_identifier)
    if result.scheme != "libra":
        raise InvalidIntentIdentifierError(
            f"Unknown intent identifier scheme {result.scheme} " f"in {encoded_intent_identifier}"
        )

    account_identifier = result.netloc
    params = parse.parse_qs(result.query)

    amount = _decode_param("amount", params, "am", lambda am: int(am))
    currency_code = _decode_param("currency code", params, "c", lambda c: str(c))

    try:
        account_address, sub_address = decode_account(account_identifier, hrp)
    except ValueError as e:
        raise InvalidIntentIdentifierError(f"decode account identifier failed: {e}:")

    return Intent(
        account_address=utils.account_address(account_address),
        sub_address=sub_address,
        currency_code=currency_code,
        amount=amount,
    )


def _decode_param(name, params, field, convert):  # pyre-ignore
    if field not in params:
        raise InvalidIntentIdentifierError(f"Can't decode {name}: not found in params {params}")

    if not isinstance(params[field], list):
        raise InvalidIntentIdentifierError(f"Can't decode {name}: unknown type {params}")

    if len(params[field]) != 1:
        raise InvalidIntentIdentifierError(f"Can't decode {name}: too many values {params}")

    value = params[field][0]
    try:
        return convert(value)
    except ValueError as e:
        raise InvalidIntentIdentifierError(f"Can't decode {name}: {value}, error: {e}")


def encode_account(
    onchain_addr: typing.Union[libra_types.AccountAddress, str],
    subaddr: typing.Optional[typing.Union[str, bytes]] = None,
    hrp: str = "tlb",
) -> str:
    """Encode onchain address and (optional) subaddress with human readable prefix(hrp) into bech32 format"""
    onchain_address_bytes = utils.account_address_bytes(onchain_addr)
    subaddress_bytes = utils.sub_address(subaddr) if subaddr else None

    try:
        encoded_address = bech32_address_encode(hrp, onchain_address_bytes, subaddress_bytes)
    except Bech32Error as e:
        raise ValueError(
            f"Can't encode from "
            f"onchain_addr: {onchain_addr}, "
            f"subaddr: {subaddr}, "
            f"hrp: {hrp}, got error: {e}"
        )
    return encoded_address


def decode_account(
    encoded_address: str, hrp: str = "tlb"
) -> typing.Tuple[libra_types.AccountAddress, typing.Optional[bytes]]:
    """Return (addrees_str, subaddress_str) given a bech32 encoded str & human readable prefix(hrp)"""
    try:
        (_version, onchain_address_bytes, subaddress_bytes) = bech32_address_decode(hrp, encoded_address)
    except Bech32Error as e:
        raise ValueError(f"Can't decode from encoded str {encoded_address}, " f"got error: {e}")

    address = utils.account_address(onchain_address_bytes)
    # If subaddress is absent, subaddress_bytes is a list of 0
    if subaddress_bytes != LIBRA_ZERO_SUBADDRESS:
        return (address, subaddress_bytes)
    return (address, None)


######################################################################################

# Bech32 implementation for Libra human readable addresses based on
# Bitcoin's segwit python lib https://github.com/fiatjaf/bech32 modified to support the
# requirements of Libra (sub)address and versioning specs.


class Bech32Error(Exception):
    """ Represents an error when creating a Libra address. """

    pass


def bech32_address_encode(hrp: str, address_bytes: bytes, subaddress_bytes: typing.Optional[bytes]) -> str:
    """Encode a Libra address (and sub-address if provided).
    Args:
        hrp: Bech32 human readable part
        address_bytes: on-chain account address (16 bytes)
        subaddress_bytes: subaddress (8 bytes). If not provided, it is set to 8 zero bytes
    Returns:
        Bech32 encoded address
    """
    # check correct hrp
    if hrp not in _LIBRA_HRP:
        raise Bech32Error(
            f"Wrong Libra address Bech32 human readable part (prefix): expected "
            f"{_LIBRA_HRP[0]} for mainnet or {_LIBRA_HRP[1]} for testnet, but {hrp} was provided"
        )

    # only accept correct size for Libra address
    if len(address_bytes) != _LIBRA_ADDRESS_SIZE:
        raise Bech32Error(f"Address size should be {_LIBRA_ADDRESS_SIZE}, but got: {len(address_bytes)}")

    # only accept correct size for Libra subaddress (if set)
    if subaddress_bytes is not None and len(subaddress_bytes) != LIBRA_SUBADDRESS_SIZE:
        raise Bech32Error(f"Subaddress size should be {LIBRA_SUBADDRESS_SIZE}, but got: {len(subaddress_bytes)}")

    encoding_version = _LIBRA_BECH32_VERSION

    # if subaddress has not been provided it's set to 8 zero bytes.
    subaddress_final_bytes = subaddress_bytes if subaddress_bytes is not None else LIBRA_ZERO_SUBADDRESS
    total_bytes = address_bytes + subaddress_final_bytes

    five_bit_data = _convertbits(total_bytes, 8, 5, True)
    # check base conversion
    if five_bit_data is None:
        raise Bech32Error("Error converting bytes to base32")
    return _bech32_encode(hrp, [encoding_version] + five_bit_data)


def bech32_address_decode(expected_hrp: str, bech32: str) -> typing.Tuple[int, bytes, bytes]:
    """Validate a Bech32 Libra address Bech32 string, and split between version, address and sub-address.
    Args:
        expected_hrp: expected Bech32 human readable part (lbr or tlb)
        bech32: Bech32 encoded address
    Returns:
        A tuple consisiting of the Bech32 version (int), address (16 bytes), subaddress (8 bytes)
    """
    len_bech32 = len(bech32)
    # check expected length
    if len_bech32 != _LIBRA_BECH32_SIZE:
        raise Bech32Error(f"Bech32 size should be {_LIBRA_BECH32_SIZE}, but it is: {len_bech32}")

    # do not allow mixed case per BIP 173
    if bech32 != bech32.lower() and bech32 != bech32.upper():
        raise Bech32Error(f"Mixed case Bech32 addresses are not allowed, got: {bech32}")
    bech32 = bech32.lower()

    # check expected hrp
    if expected_hrp not in _LIBRA_HRP:
        raise Bech32Error(
            f'Wrong Libra address Bech32 human readable part (prefix): expected "{LBR}" '
            f'for mainnet or "{TLB}" for testnet but got "{bech32[:3]}"'
        )

    if bech32[:3] != expected_hrp:
        raise Bech32Error(
            f'Wrong Libra address Bech32 human readable part (prefix): requested "{expected_hrp}" but '
            f'got "{bech32[:3]}"'
        )

    # check separator
    if bech32[3] != _BECH32_SEPARATOR:
        raise Bech32Error(f"Non-expected Bech32 separator: {bech32[3]}")

    # check characters after separator in Bech32 alphabet
    if not all(x in _BECH32_CHARSET for x in bech32[4:]):
        raise Bech32Error(f"Invalid Bech32 characters detected: {bech32}")
    hrp = bech32[:3]

    # version is defined by the index of the Bech32 character after separator
    address_version = _BECH32_CHARSET.find(bech32[4])
    # check valid version
    if address_version != _LIBRA_BECH32_VERSION:
        raise Bech32Error(f"Version mismatch. Expected {_LIBRA_BECH32_VERSION}, " f"but received {address_version}")

    # we've already checked that all characters are in the correct alphabet,
    # thus, this will always succeed
    data = [_BECH32_CHARSET.find(x) for x in bech32[5:]]

    # check Bech32 checksum
    if not _bech32_verify_checksum(hrp, [address_version] + data):
        raise Bech32Error(f"Bech32 checksum validation failed: {bech32}")

    decoded_data = _convertbits(data[:-_BECH32_CHECKSUM_CHAR_SIZE], 5, 8, False)
    # check base conversion
    if decoded_data is None:
        raise Bech32Error("Error converting bytes from base32")

    length_data = len(decoded_data)
    # extra check about the expected output (sub)address size in bytes
    if length_data != _LIBRA_ADDRESS_SIZE + LIBRA_SUBADDRESS_SIZE:
        raise Bech32Error(
            f"Expected {_LIBRA_ADDRESS_SIZE + LIBRA_SUBADDRESS_SIZE} bytes after decoding, but got: {length_data}"
        )

    return (
        address_version,
        bytes(decoded_data[:_LIBRA_ADDRESS_SIZE]),
        bytes(decoded_data[-LIBRA_SUBADDRESS_SIZE:]),
    )


def _bech32_polymod(values: typing.Iterable[int]) -> int:
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def _bech32_hrp_expand(hrp: str) -> typing.List[int]:
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _bech32_verify_checksum(hrp: str, data: typing.Iterable[int]) -> bool:
    """Verify a checksum given HRP and converted data characters."""
    return _bech32_polymod(_bech32_hrp_expand(hrp) + list(data)) == 1


def _bech32_create_checksum(hrp: str, data: typing.Iterable[int]) -> typing.List[int]:
    """Compute the checksum values given HRP and data."""
    values = _bech32_hrp_expand(hrp) + list(data)
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def _bech32_encode(hrp: str, data: typing.Iterable[int]) -> str:
    """Compute a Bech32 string given HRP and data values."""
    combined = list(data) + _bech32_create_checksum(hrp, data)
    return hrp + _BECH32_SEPARATOR + "".join([_BECH32_CHARSET[d] for d in combined])


def _convertbits(
    data: typing.Iterable[int], from_bits: int, to_bits: int, pad: bool
) -> typing.Optional[typing.List[int]]:
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1
    for value in data:
        if value < 0 or (value >> from_bits):
            return None
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (to_bits - bits)) & maxv)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & maxv):
        return None
    return ret
