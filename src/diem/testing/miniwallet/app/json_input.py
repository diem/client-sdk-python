# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Optional, Type, TypeVar, Dict, Callable, Any, Awaitable


T = TypeVar("T")
Validator = Callable[[str, T], Awaitable[None]]


@dataclass
class JsonInput:
    data: Dict[str, Any]

    async def get_nullable(self, name: str, klass: Type[T], validator: Optional[Validator] = None) -> Optional[T]:
        val = self.data.get(name, None)
        if val is None:
            return None
        if isinstance(val, klass):
            if validator:
                await validator(name, val)
            return val
        raise ValueError("%r type must be %r, but got %r" % (name, klass.__name__, type(val).__name__))

    async def get(self, name: str, klass: Type[T], validator: Optional[Validator] = None) -> T:
        val = await self.get_nullable(name, klass, validator)
        if val is None:
            raise ValueError("%r is required" % name)
        return val
