# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Optional, Type, TypeVar, Dict, Callable, Any


T = TypeVar("T")
Validator = Callable[[str, T], None]


@dataclass
class JsonInput:
    data: Dict[str, Any]

    def get_nullable(self, name: str, typ: Type[T], validator: Optional[Validator] = None) -> Optional[T]:
        val = self.data.get(name, None)
        if val is None:
            return None
        if isinstance(val, typ):
            if validator:
                validator(name, val)
            return val
        raise ValueError("%r type must be %r, but got %r" % (name, typ.__name__, type(val).__name__))

    def get(self, name: str, typ: Type[T], validator: Optional[Validator] = None) -> T:
        val = self.get_nullable(name, typ, validator)
        if val is None:
            raise ValueError("%r is required" % name)
        return val
