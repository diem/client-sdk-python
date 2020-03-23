# pyre-strict

from abc import ABC


class AccountResource(ABC):
    @property
    def address(self) -> bytes:
        """Account address in bytes"""
        raise NotImplementedError()

    @property
    def balance(self) -> int:
        """Account balance"""
        raise NotImplementedError()

    @property
    def sequence(self) -> int:
        """Account sequence number"""
        raise NotImplementedError()

    @property
    def authentication_key(self) -> bytes:
        """Account authentication key, could be different than account address"""
        raise NotImplementedError()

    @property
    def delegated_key_rotation_capability(self) -> bool:
        """delegated_key_rotation_capability"""
        raise NotImplementedError()

    @property
    def delegated_withdrawal_capability(self) -> bool:
        """delegated_withdrawal_capability"""
        raise NotImplementedError()

    @property
    def sent_events_key(self) -> bytes:
        """sent_events"""
        raise NotImplementedError()

    @property
    def received_events_key(self) -> bytes:
        """received_events"""
        raise NotImplementedError()


class AccountKey(ABC):
    @property
    def address(self) -> bytes:
        raise NotImplementedError()

    @property
    def authentication_key(self) -> bytes:
        raise NotImplementedError()

    @property
    def public_key(self) -> bytes:
        raise NotImplementedError()

    @property
    def private_key(self) -> bytes:
        raise NotImplementedError()


class SignedTransaction(ABC):
    @property
    def sender(self) -> bytes:
        raise NotImplementedError()

    @property
    def sequence(self) -> int:
        raise NotImplementedError()

    @property
    def max_gas_amount(self) -> int:
        raise NotImplementedError()

    @property
    def gas_unit_price(self) -> int:
        raise NotImplementedError()

    @property
    def expiration_time(self) -> int:
        raise NotImplementedError()

    @property
    def is_p2p(self) -> bool:
        raise NotImplementedError()

    @property
    def is_mint(self) -> bool:
        raise NotImplementedError()

    @property
    def receiver(self) -> bytes:
        raise NotImplementedError()

    @property
    def amount(self) -> int:
        raise NotImplementedError()

    @property
    def public_key(self) -> bytes:
        raise NotImplementedError()

    @property
    def signature(self) -> bytes:
        raise NotImplementedError()

    @property
    def version(self) -> int:
        raise NotImplementedError()

    @property
    def gas(self) -> int:
        raise NotImplementedError()


class Event(ABC):
    @property
    def module(self) -> str:
        raise NotImplementedError()

    @property
    def name(self) -> str:
        raise NotImplementedError()


class PaymentEvent(Event, ABC):
    @property
    def is_sent(self) -> bool:
        raise NotImplementedError()

    @property
    def is_received(self) -> bool:
        raise NotImplementedError()

    @property
    def sender_address(self) -> bytes:
        raise NotImplementedError()

    @property
    def receiver_address(self) -> bytes:
        raise NotImplementedError()

    @property
    def amount(self) -> int:
        raise NotImplementedError()

    @property
    def metadata(self) -> bytes:
        raise NotImplementedError()
