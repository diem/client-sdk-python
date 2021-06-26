# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines util functions for encoding and decoding offchain specific JWS messages.

The `serialize` and `deserialize` functions handle JWS message with the following requirements:

  1. Protected header must be `{"alg": "EdDSA"}`
  2. Characters encoding must be `utf-8`
  3. JWS encoding must be `compact`

"""

import typing

from . import CommandRequestObject, CommandResponseObject, to_json, from_json
from .. import jws


T = typing.TypeVar("T")


def serialize(
    obj: typing.Union[CommandRequestObject, CommandResponseObject],
    sign: typing.Callable[[bytes], bytes],
) -> bytes:
    return jws.encode(to_json(obj), sign)


def deserialize(
    msg: bytes,
    klass: typing.Type[T],
    verify: typing.Callable[[bytes, bytes], None],
) -> T:
    _, body = jws.decode(msg, verify)
    return from_json(body, klass)
