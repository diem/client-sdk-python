# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module defines `ReferenceIDCommand` class provides utils for processing `ReferenceIDCommand` properly."""

import dataclasses, uuid
from .types import (
    ReferenceIDCommandObject,
)


@dataclasses.dataclass(frozen=True)
class ReferenceIDCommand:
    """Wrapper object of `ReferenceIDCommand` with request information

    Defined in DIP-10: https://github.com/diem/dip/blob/main/dips/dip-10.md
    """

    reference_id_command_object: ReferenceIDCommandObject
    cid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    @staticmethod
    def init(
        sender: str,
        sender_address: str,
        receiver: str,
        reference_id: str,
    ) -> "ReferenceIDCommand":
        """init functon initializes a new `ReferenceIDCommand` for starting the DiemID to address resolution"""

        return ReferenceIDCommand(
            reference_id_command_object=ReferenceIDCommandObject(
                sender=sender, sender_address=sender_address, receiver=receiver, reference_id=reference_id
            )
        )

    def id(self) -> str:
        """returns `cid` from the request object"""
        return self.cid

    def reference_id(self) -> str:
        """returns `reference_id` of `ReferenceIDCommand`"""

        return self.reference_id_command_object.reference_id

    def sender(self) -> str:
        """returns sender pay address"""

        return self.reference_id_command_object.sender

    def receiver(self) -> str:
        """returns receiver pay address"""

        return self.reference_id_command_object.receiver

    def sender_address(self) -> str:
        """returns sender address"""

        return self.reference_id_command_object.sender_address
