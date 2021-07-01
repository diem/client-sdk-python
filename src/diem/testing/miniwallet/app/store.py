# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Type, Any, Callable, TypeVar, Generator
from .models import Base, Account, Event
from .... import utils
import json, time


T = TypeVar("T", bound=Base)


class NotFoundError(ValueError):
    pass


@dataclass
class InMemoryStore:
    """InMemoryStore is a simple in-memory store for resources"""

    resources: Dict[Type[Base], List[Dict[str, Any]]] = field(default_factory=dict)
    gen_id: int = field(default=0)

    def next_id(self) -> int:
        self.gen_id += 1
        return self.gen_id

    def create_event(self, account_id: str, type: str, data: str) -> Event:
        return self.create(Event, account_id=account_id, type=type, data=data, timestamp=_ts())

    def find(self, klass: Type[T], **conds: Any) -> T:
        list = self._select(klass, **conds)
        ret = next(list, None)
        if not ret:
            raise NotFoundError("%s not found by %s" % (klass.__name__, conds))
        if next(list, None):
            raise ValueError("found multiple resources data matches %s" % conds)
        return ret

    def find_all(self, klass: Type[T], **conds: Any) -> List[T]:
        return list(self._select(klass, **conds))

    def create(self, klass: Type[T], before_create: Callable[[Dict[str, Any]], None] = lambda _: _, **data: Any) -> T:
        before_create(data)
        obj = klass(**self._insert(klass, **data))
        self._record_event(obj, "created", data)
        return obj

    def update(self, obj: T, before_update: Callable[[T], None] = lambda _: _, **data: Any) -> None:
        for k, v in data.items():
            setattr(obj, k, v)
        before_update(obj)
        self._update(obj)
        self._record_event(obj, "updated", data)

    def _record_event(self, obj: T, action: str, data: Dict[str, Any]) -> None:
        if not isinstance(obj, Event):
            type = "%s_%s" % (action, utils.to_snake(obj))
            account_id = obj.id if isinstance(obj, Account) else obj.account_id  # pyre-ignore
            data["id"] = obj.id
            self._insert(Event, account_id=account_id, type=type, data=json.dumps(data), timestamp=_ts())

    def _update(self, obj: T) -> None:
        records = self.resources.get(type(obj), [])
        index = next(iter([i for i, res in enumerate(records) if res["id"] == obj.id]), None)
        if index is None:
            raise NotFoundError("could not find resource by id: %s" % obj.id)
        records[index] = asdict(obj)

    def _insert(self, klass: Type[T], **res: Any) -> Dict[str, Any]:
        if "id" not in res:
            res["id"] = str(self.next_id())
        self.resources.setdefault(klass, []).append(asdict(klass(**res)))
        return res

    def _select(self, klass: Type[T], reverse: bool = False, **conds: Any) -> Generator[T, None, None]:
        items = reversed(self.resources.get(klass, [])) if reverse else self.resources.get(klass, [])
        for res in items:
            if _match(res, **conds):
                yield klass(**res)


def _match(res: Dict[str, Any], **conds: Any) -> bool:
    for k, v in conds.items():
        if res.get(k) != v:
            return False
    return True


def _ts() -> int:
    return int(time.time() * 1000)
