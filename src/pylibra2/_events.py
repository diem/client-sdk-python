import typing

from calibra.lib.clients.pylibra2.json_rpc.types import (
    Event,
    ReceivedPaymentEventData,
    SentPaymentEventData,
)


class LibraEvent:
    _event: Event

    def __init__(self, event: Event):
        self._event = event

    @property
    def type(self) -> str:
        return self._event.data.type

    @property
    def key(self) -> bytes:
        return bytes.fromhex(self._event.key)

    @property
    def sequence(self) -> int:
        return self._event.sequence_number

    @property
    def version(self) -> int:
        return self._event.transaction_version

    def __str__(self):
        return f"{self._event}"


class LibraPaymentEvent(LibraEvent):
    _payment_event: typing.Union[SentPaymentEventData, ReceivedPaymentEventData]

    def __init__(self, event: Event):
        super().__init__(event)
        if isinstance(event.data, SentPaymentEventData):
            self._payment_event = typing.cast(SentPaymentEventData, event.data)
        if isinstance(event.data, ReceivedPaymentEventData):
            self._payment_event = typing.cast(ReceivedPaymentEventData, event.data)

    @property
    def sender(self) -> bytes:
        return bytes.fromhex(self._payment_event.sender)

    @property
    def receiver(self) -> bytes:
        return bytes.fromhex(self._payment_event.receiver)

    @property
    def currency(self) -> str:
        return self._payment_event.amount.currency

    @property
    def amount(self) -> int:
        return self._payment_event.amount.amount

    @property
    def metadata(self) -> bytes:
        return bytes.fromhex(self._payment_event.metadata)


class LibraUnknownEvent(LibraEvent):
    def __init__(self, event: Event):
        super().__init__(event)
