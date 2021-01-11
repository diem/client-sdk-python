# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod

from . import CommandRequestObject
from .action import Action

import typing


class Command(ABC):
    @abstractmethod
    def command_type(self) -> str:
        ...

    @abstractmethod
    def id(self) -> str:
        ...

    @abstractmethod
    def follow_up_action(self) -> typing.Optional[Action]:
        ...

    @abstractmethod
    def reference_id(self) -> str:
        ...

    @abstractmethod
    def validate(self, prior: typing.Optional["Command"]) -> None:
        ...

    @abstractmethod
    def my_address(self) -> str:
        ...

    @abstractmethod
    def opponent_address(self) -> str:
        ...

    @abstractmethod
    def new_request(self) -> CommandRequestObject:
        ...
