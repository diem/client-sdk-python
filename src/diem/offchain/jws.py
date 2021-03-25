# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines util functions for encoding and decoding offchain specific JWS messages.

The `serialize` and `deserialize` functions handle JWS message with the following requirements:

  1. Protected header must be `{"alg": "EdDSA"}`
  2. Characters encoding must be `utf-8`
  3. JWS encoding must be `compact`

"""

import base64, typing

from . import CommandRequestObject, CommandResponseObject, to_json, from_json


PROTECTED_HEADER: bytes = base64.urlsafe_b64encode(b'{"alg":"EdDSA"}')
ENCODING: str = "UTF-8"

T = typing.TypeVar("T")


def serialize(
    obj: typing.Union[CommandRequestObject, CommandResponseObject],
    sign: typing.Callable[[bytes], bytes],
) -> bytes:
    return serialize_string(to_json(obj), sign)


def deserialize(
    msg: bytes,
    klass: typing.Type[T],
    verify: typing.Callable[[bytes, bytes], None],
) -> T:
    decoded_body, sig, signing_msg = deserialize_string(msg)

    verify(sig, signing_msg)
    return from_json(decoded_body, klass)


def serialize_string(json: str, sign: typing.Callable[[bytes], bytes]) -> bytes:
    payload = base64.urlsafe_b64encode(json.encode(ENCODING))
    msg = signing_message(payload)
    return b".".join([msg, base64.urlsafe_b64encode(sign(msg))])


def deserialize_string(msg: bytes) -> typing.Tuple[str, bytes, bytes]:
    text = msg.decode(ENCODING)
    parts = text.split(".")
    if len(parts) != 3:
        raise ValueError("invalid JWS compact message: %s, expect 3 parts: <header>.<payload>.<signature>" % text)

    header, body, sig = parts
    if header.encode(ENCODING) != PROTECTED_HEADER:
        raise ValueError(f"invalid JWS message header: {header}, expect {PROTECTED_HEADER}")

    body_bytes = body.encode(ENCODING)
    return (
        decode(body_bytes).decode(ENCODING),
        decode(sig.encode(ENCODING)),
        signing_message(body_bytes),
    )


def signing_message(payload: bytes) -> bytes:
    return b".".join([PROTECTED_HEADER, payload])


def decode(msg: bytes) -> bytes:
    return base64.urlsafe_b64decode(fix_padding(msg))


def fix_padding(input: bytes) -> bytes:
    return input + b"=" * (4 - (len(input) % 4))
