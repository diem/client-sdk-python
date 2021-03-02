# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""DIP-5 Diem Account Identifier and Intent Identifier Utilities.

See https://dip.diem.com/dip-5 for more details

"""


import typing
from urllib import parse
from typing import List

from . import bech32
from .. import diem_types, utils, chain_ids

from .bech32 import bech32_address_encode, bech32_address_decode, Bech32Error, _DIEM_BECH32_SIZE
from .subaddress import DIEM_SUBADDRESS_SIZE, DIEM_ZERO_SUBADDRESS, gen_subaddress

DM = "dm"  # mainnet
TDM = "tdm"  # testnet
PDM = "pdm"  # premainnet
DDM = "ddm"  # dry-run mainnet

HRPS: typing.Dict[int, str] = {
    chain_ids.MAINNET.to_int(): DM,
    chain_ids.TESTNET.to_int(): TDM,
    chain_ids.DEVNET.to_int(): TDM,
    chain_ids.TESTING.to_int(): TDM,
}


class InvalidIntentIdentifierError(Exception):
    pass


class Intent:
    """Intent is a struct hold data decoded from Diem Intent Identifier string"""

    account_address: diem_types.AccountAddress
    sub_address: typing.Optional[bytes]
    currency_code: typing.Optional[str]
    amount: typing.Optional[int]

    def __init__(
        self,
        account_address: diem_types.AccountAddress,
        sub_address: typing.Optional[bytes],
        currency_code: typing.Optional[str],
        amount: typing.Optional[int],
        hrp: str,
    ) -> None:
        self.account_address = account_address
        self.sub_address = sub_address
        self.currency_code = currency_code
        self.amount = amount
        self.hrp = hrp

    @property
    def subaddress(self) -> typing.Optional[bytes]:
        return self.sub_address

    @property
    def account_address_bytes(self) -> bytes:
        return self.account_address.to_bytes()

    @property
    def account_id(self) -> str:
        return encode_account(self.account_address, self.sub_address, self.hrp)


def encode_intent(
    encoded_account_identifier: str, currency_code: typing.Optional[str] = None, amount: typing.Optional[int] = None
) -> str:
    """
    Encode account identifier string(encoded), currency code and amount into
    Diem intent identifier (https://dip.diem.com/dip-5/)
    """

    params = []
    if currency_code:
        params.append("c=%s" % currency_code)
    if amount is not None and amount > 0:
        params.append("am=%s" % amount)
    if params:
        return "diem://%s?%s" % (encoded_account_identifier, "&".join(params))
    return "diem://%s" % encoded_account_identifier


def decode_intent(encoded_intent_identifier: str, hrp: str) -> Intent:
    """
    Decode Diem intent identifier (https://dip.diem.com/dip-5/) int 3 parts:
    1. account identifier: account address & sub-address
    2. currency code
    3. amount

    InvalidIntentIdentifierError is raised if given identifier is invalid
    """

    result = parse.urlparse(encoded_intent_identifier)
    if result.scheme != "diem":
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
        hrp=hrp,
    )


def _decode_param(name, params, field, convert):  # pyre-ignore
    if field not in params:
        return None

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
    onchain_addr: typing.Union[diem_types.AccountAddress, str],
    subaddr: typing.Union[str, bytes, None],
    hrp: str,
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


def decode_account(encoded_address: str, hrp: str) -> typing.Tuple[diem_types.AccountAddress, typing.Optional[bytes]]:
    """Return (addrees_str, subaddress_str) given a bech32 encoded str & human readable prefix(hrp)"""
    try:
        (_version, onchain_address_bytes, subaddress_bytes) = bech32.bech32_address_decode(hrp, encoded_address)
    except Bech32Error as e:
        raise ValueError(f"Can't decode from encoded str {encoded_address}, " f"got error: {e}")

    address = utils.account_address(onchain_address_bytes)
    # If subaddress is absent, subaddress_bytes is a list of 0
    if subaddress_bytes != DIEM_ZERO_SUBADDRESS:
        return (address, subaddress_bytes)
    return (address, None)


def decode_hrp(encoded_address: str) -> str:
    if len(encoded_address) not in _DIEM_BECH32_SIZE:
        raise ValueError("Invalid account identifier address size: {encoded_address}")
    if encoded_address[:2] == DM:
        return DM
    return encoded_address[:3]


def decode_account_address(encoded_address: str, hrp: str) -> diem_types.AccountAddress:
    address, _ = decode_account(encoded_address, hrp)
    return address


def decode_account_subaddress(encoded_address: str, hrp: str) -> typing.Optional[bytes]:
    _, subaddress = decode_account(encoded_address, hrp)
    return subaddress
