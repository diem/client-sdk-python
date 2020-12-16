# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from .action import Action

import typing


class Command(ABC):
    @abstractmethod
    def id(self) -> str:
        ...

    @abstractmethod
    def is_inbound(self) -> bool:
        ...

    @abstractmethod
    def follow_up_action(self) -> typing.Optional[Action]:
        ...

    @abstractmethod
    def reference_id(self) -> str:
        ...

    @abstractmethod
    def new_command(self) -> "Command":
        """sub-class should define **kwargs for creating new command from current instance"""
        ...

    @abstractmethod
    def validate(self, prior: typing.Optional["Command"]) -> None:
        ...
