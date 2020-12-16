# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from .types import (
    OffChainErrorType,
    OffChainErrorObject,
)

import typing


class Error(Exception):
    obj: OffChainErrorObject

    def __init__(self, obj: OffChainErrorObject) -> None:
        super(Exception, self).__init__(obj)
        self.obj = obj


def command_error(code: str, message: str, field: typing.Optional[str] = None) -> Error:
    return Error(
        obj=OffChainErrorObject(
            type=OffChainErrorType.command_error,
            code=code,
            field=field,
            message=message,
        )
    )


def protocol_error(code: str, message: str, field: typing.Optional[str] = None) -> Error:
    return Error(
        obj=OffChainErrorObject(
            type=OffChainErrorType.protocol_error,
            code=code,
            field=field,
            message=message,
        )
    )
