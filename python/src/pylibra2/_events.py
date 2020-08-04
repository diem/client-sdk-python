import typing

from calibra.lib.clients.pylibra2.json_rpc.types import (
    Event,
    ReceivedPaymentEvent,
    SentPaymentEvent,
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


class LibraSentPaymentEvent(LibraEvent):
    _sent_payment_event: SentPaymentEvent

    def __init__(self, event: Event):
        super().__init__(event)
        self._sent_payment_event = typing.cast(SentPaymentEvent, event.data)

    # TODO (ssinghaldev) T69790014 Add fields once it becomes available on testnet
    @property
    def sender(self) -> bytes:
        raise NotImplementedError

    @property
    def receiver(self) -> bytes:
        return bytes.fromhex(self._sent_payment_event.receiver)

    @property
    def currency(self) -> str:
        return self._sent_payment_event.amount.currency

    @property
    def amount(self) -> int:
        return self._sent_payment_event.amount.amount

    @property
    def metadata(self) -> bytes:
        return bytes.fromhex(self._sent_payment_event.metadata)


class LibraReceivedPaymentEvent(LibraEvent):
    _received_payment_event: ReceivedPaymentEvent

    def __init__(self, event: Event):
        super().__init__(event)
        self._received_payment_event = typing.cast(ReceivedPaymentEvent, event.data)

    @property
    def sender(self) -> bytes:
        return bytes.fromhex(self._received_payment_event.sender)

    # TODO (ssinghaldev) T69790014 Add fields once it becomes available on testnet
    @property
    def receiver(self) -> bytes:
        raise NotImplementedError

    @property
    def currency(self) -> str:
        return self._received_payment_event.amount.currency

    @property
    def amount(self) -> int:
        return self._received_payment_event.amount.amount

    @property
    def metadata(self) -> bytes:
        return bytes.fromhex(self._received_payment_event.metadata)


class LibraUnknownEvent(LibraEvent):
    def __init__(self, event: Event):
        super().__init__(event)
