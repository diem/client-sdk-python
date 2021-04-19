# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines util functions for encoding and decoding offchain specific JWS messages.

The `serialize` and `deserialize` functions handle JWS message with the following requirements:

  1. Protected header must be `{"alg": "EdDSA"}`
  2. Characters encoding must be `utf-8`
  3. JWS encoding must be `compact`

"""

import base64, json, typing

from . import CommandRequestObject, CommandResponseObject, to_json, from_json


PROTECTED_HEADER: bytes = base64.urlsafe_b64encode(b'{"alg":"EdDSA"}')
ENCODING: str = "UTF-8"

T = typing.TypeVar("T")


def serialize(
    obj: typing.Union[CommandRequestObject, CommandResponseObject],
    sign: typing.Callable[[bytes], bytes],
    headers: typing.Optional[typing.Dict[str, typing.Any]] = None,
) -> bytes:
    return serialize_string(to_json(obj), sign, headers=headers)


def deserialize(
    msg: bytes,
    klass: typing.Type[T],
    verify: typing.Callable[[bytes, bytes], None],
) -> T:
    decoded_body, sig, signing_msg = deserialize_string(msg)
    verify(sig, signing_msg)
    return from_json(decoded_body, klass)


def serialize_string(
    json: str, sign: typing.Callable[[bytes], bytes], headers: typing.Optional[typing.Dict[str, typing.Any]] = None
) -> bytes:
    header = PROTECTED_HEADER if headers is None else encode_headers(headers)
    payload = base64.urlsafe_b64encode(json.encode(ENCODING))
    sig = sign(signing_message(payload, header=header))
    return b".".join([header, payload, base64.urlsafe_b64encode(sig)])


def deserialize_string(msg: bytes) -> typing.Tuple[str, bytes, bytes]:
    parts = msg.split(b".")
    if len(parts) != 3:
        raise ValueError(
            "invalid JWS compact message: %s, expect 3 parts: <header>.<payload>.<signature>" % msg.decode(ENCODING)
        )

    header, body, sig = parts
    header_text = decode(header).decode(ENCODING)
    try:
        protected_headers = json.loads(header_text)
    except json.decoder.JSONDecodeError as e:
        raise ValueError(f"invalid JWS message header: {header_text}") from e

    if not isinstance(protected_headers, dict) or protected_headers.get("alg") != "EdDSA":
        raise ValueError(f"invalid JWS message header: {header}, expect alg is EdDSA")

    return (
        decode(body).decode(ENCODING),
        decode(sig),
        signing_message(body, header=header),
    )


def signing_message(payload: bytes, header: bytes) -> bytes:
    return b".".join([header, payload])


def encode_headers(headers: typing.Dict[str, typing.Any]) -> bytes:
    return base64.urlsafe_b64encode(json.dumps(headers).encode(ENCODING))


def decode(msg: bytes) -> bytes:
    return base64.urlsafe_b64decode(fix_padding(msg))


def fix_padding(input: bytes) -> bytes:
    return input + b"=" * (4 - (len(input) % 4))
