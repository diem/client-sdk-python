# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from .action import Action
from .types import CommandRequestObject
from .. import identifier

import typing


class Command(ABC):
    @abstractmethod
    def id(self) -> str:
        """Returns a global unique id of the command object

        Subclass may call `make_global_unique_id` to create the unique id.

        Caller should not assume the format of this id, please refer to sub-classes for implementation
        details.

        The address should not include subaddress, it can include account identifier hrp.
        """
        ...

    @abstractmethod
    def cid(self) -> str:
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
    def opponent_address(self) -> str:
        """Returns the opponent account identifier that receives the command request"""
        ...

    def make_global_unique_id(
        self, initial_sender_account_identifier: str, initial_receiver_account_identifier: str
    ) -> str:
        """Returns a global unique id combined by hrp, sender receiver addresses and reference id.

        Format: "{hrp}_{initial sender onchain account address hex}_{initial receiver onchain account address hex}_{reference id}"
        """

        hrp = identifier.decode_hrp(initial_sender_account_identifier)
        sender = identifier.decode_account_address(initial_sender_account_identifier, hrp)
        receiver = identifier.decode_account_address(initial_receiver_account_identifier, hrp)
        return "%s_%s_%s_%s" % (hrp, sender.to_hex(), receiver.to_hex(), self.reference_id())
