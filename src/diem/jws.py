# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines util functions for encoding and decoding offchain specific JWS messages.

The `encode` and `decode` functions handle JWS message with the following requirements:

  1. Protected header must include `{"alg": "EdDSA"}`
  2. Characters encoding must be `utf-8`
  3. JWS encoding must be `compact` (https://datatracker.ietf.org/doc/html/rfc7515#section-7.1)

"""

from typing import Any, Callable, Dict, Tuple
import base64, json


ENCODING: str = "UTF-8"
DIEM_ALG: str = "EdDSA"


class InvalidHeaderError(ValueError):
    def __init__(self, header: str) -> None:
        super().__init__("invalid JWS message header: %s" % header)


def encode(
    msg: str,
    sign: Callable[[bytes], bytes],
    headers: Dict[str, Any] = {"alg": DIEM_ALG},
    content_detached: bool = False,
) -> bytes:
    header = encode_headers(headers)
    payload = encode_b64url(msg.encode(ENCODING))
    sig = sign(signing_message(payload, header))
    if content_detached:
        payload = b""
    return b".".join([header, payload, encode_b64url(sig)])


def decode(
    msg: bytes, verify: Callable[[bytes, bytes], None], detached_content: bytes = b""
) -> Tuple[Dict[str, Any], str]:
    parts = msg.split(b".")
    if len(parts) != 3:
        raise ValueError("invalid JWS compact message: %s" % msg)

    header, body, sig = parts

    if detached_content and not body:
        body = encode_b64url(detached_content)

    try:
        header_text = decode_b64url(header).decode(ENCODING)
    except ValueError as e:
        raise InvalidHeaderError(str(header)) from e

    try:
        protected_headers = json.loads(header_text)
    except ValueError as e:
        raise InvalidHeaderError(header_text) from e

    if not isinstance(protected_headers, dict) or protected_headers.get("alg") != DIEM_ALG:
        raise InvalidHeaderError(header_text)

    verify(decode_b64url(sig), signing_message(body, header))

    return (protected_headers, decode_b64url(body).decode(ENCODING))


def signing_message(payload: bytes, header: bytes) -> bytes:
    return b".".join([header, payload])


def encode_headers(headers: Dict[str, Any]) -> bytes:
    return encode_b64url(json.dumps(headers, separators=(",", ":")).encode(ENCODING))


def encode_b64url(msg: bytes) -> bytes:
    return base64.urlsafe_b64encode(msg).rstrip(b"=")


def decode_b64url(msg: bytes) -> bytes:
    return base64.urlsafe_b64decode(fix_padding(msg))


def fix_padding(input: bytes) -> bytes:
    return input + b"=" * (4 - (len(input) % 4))
