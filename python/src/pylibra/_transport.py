# pyre-strict

import typing
from abc import ABC
import dataclasses

from . import NETWORK_DEFAULT
from ._types import AccountResource, SignedTransaction, Event, PaymentEvent


@dataclasses.dataclass
class ClientError(Exception):
    message: str


@dataclasses.dataclass
class SubmitTransactionError(Exception):
    code: int
    message: str
    data: dict


class BaseLibraNetwork(ABC):
    def __init__(self, network: str = NETWORK_DEFAULT):
        raise NotImplementedError()

    def currentTimestampUsecs(self) -> int:
        """Get latest block timestamp from the network."""
        raise NotImplementedError()

    def getAccount(self, address_hex: str) -> typing.Optional[AccountResource]:
        """Get AccountResource for given address."""
        raise NotImplementedError()

    def sendTransaction(self, signed_transaction_bytes: bytes) -> None:
        raise NotImplementedError()

    def transactions_by_range(
        self, start_version: int, limit: int, include_events: bool = False
    ) -> typing.List[typing.Tuple[SignedTransaction, typing.List[typing.Union[Event, PaymentEvent]]]]:
        raise NotImplementedError()

    def transaction_by_acc_seq(
        self, addr_hex: str, seq: int, include_events: bool = False
    ) -> typing.Tuple[typing.Optional[SignedTransaction], typing.List[typing.Union[Event, PaymentEvent]]]:
        raise NotImplementedError()

    def get_events(self, key_hex: str, start: int, limit: int) -> typing.List[typing.Union[Event, PaymentEvent]]:
        raise NotImplementedError()
