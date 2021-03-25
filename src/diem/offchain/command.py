# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from .action import Action
from .types import CommandRequestObject

import typing


class Command(ABC):
    """Command defines common interface for all commands """

    @abstractmethod
    def id(self) -> str:
        """Returns cid of command object"""
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
    def new_request(self) -> CommandRequestObject:
        ...

    @abstractmethod
    def validate(self, prior: typing.Optional["Command"]) -> None:
        ...

    @abstractmethod
    def my_address(self) -> str:
        """Returns my account identifier used for sending command request"""
        ...

    @abstractmethod
    def counterparty_address(self) -> str:
        """Returns the counterparty account identifier that receives the command request"""
        ...
