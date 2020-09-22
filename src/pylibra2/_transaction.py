import typing

from calibra.lib.clients.pylibra2._events import (
    LibraEvent,
    LibraPaymentEvent,
    LibraUnknownEvent,
)
from calibra.lib.clients.pylibra2.json_rpc.types import (
    BlockMetadataTransactionData,
    MintTransactionScript,
    PeerToPeerTransactionScript,
    ReceivedPaymentEventData,
    Script,
    SentPaymentEventData,
    Transaction,
    UnknownEventData,
    UnknownTransactionScript,
    UserTransactionData,
    VMStatus,
)


class LibraScript:
    def __init__(self, type: str):
        self._type = type

    @property
    def type(self) -> str:
        return self._type


class LibraP2PScript(LibraScript):
    _p2p_script: PeerToPeerTransactionScript

    def __init__(self, script: Script):
        super().__init__(script.type)
        self._p2p_script = typing.cast(PeerToPeerTransactionScript, script)

    @property
    def receiver(self) -> str:
        return self._p2p_script.receiver

    @property
    def currency(self) -> str:
        return self._p2p_script.currency

    @property
    def amount(self) -> int:
        return self._p2p_script.amount

    @property
    def metadata(self) -> bytes:
        return bytes.fromhex(self._p2p_script.metadata)

    @property
    def metadata_signature(self) -> bytes:
        return bytes.fromhex(self._p2p_script.metadata_signature)


class LibraMintScript(LibraScript):
    _mint_script: MintTransactionScript

    def __init__(self, script: Script):
        super().__init__(script.type)
        self._mint_script = typing.cast(MintTransactionScript, script)

    @property
    def receiver(self) -> str:
        return self._mint_script.receiver

    @property
    def authkey_prefix(self) -> bytes:
        return bytes.fromhex(self._mint_script.auth_key_prefix)

    @property
    def amount(self) -> int:
        return self._mint_script.amount


class LibraUnknownScript(LibraScript):
    def __init__(self, script):
        super().__init__(script.type)


class LibraTransaction:
    _tx_resp: Transaction
    _events: typing.List[LibraEvent]

    def __init__(self, transaction_resp: Transaction):
        self._tx_resp = transaction_resp
        self._events = []

        for event in self._tx_resp.events:
            if isinstance(event.data, SentPaymentEventData) or isinstance(
                event.data, ReceivedPaymentEventData
            ):
                self._events.append(typing.cast(LibraEvent, LibraPaymentEvent(event)))
            elif isinstance(event.data, UnknownEventData):
                self._events.append(typing.cast(LibraEvent, LibraUnknownEvent(event)))

    @property
    def type(self) -> str:
        return self._tx_resp.transaction.type

    @property
    def events(self) -> typing.List[LibraEvent]:
        return self._events

    @property
    def version(self) -> int:
        return self._tx_resp.version

    @property
    def vm_status(self) -> VMStatus:
        return self._tx_resp.vm_status

    @property
    def gas_used(self) -> int:
        return self._tx_resp.gas_used

    @property
    def hash(self) -> bytes:
        return bytes.fromhex(self._tx_resp.hash)

    @property
    def bytes_(self) -> bytes:
        return bytes.fromhex(self._tx_resp.bytes)


class LibraUserTransaction(LibraTransaction):
    _user_tx: UserTransactionData
    _script: LibraScript

    def __init__(self, transaction_resp: Transaction):
        super().__init__(transaction_resp)

        self._user_tx = typing.cast(UserTransactionData, transaction_resp.transaction)

        if isinstance(self._user_tx.script, PeerToPeerTransactionScript):
            self._script = typing.cast(
                LibraScript, LibraP2PScript(self._user_tx.script)
            )
        elif isinstance(self._user_tx.script, MintTransactionScript):
            self._script = typing.cast(
                LibraScript, LibraMintScript(self._user_tx.script)
            )
        elif isinstance(self._user_tx.script, UnknownTransactionScript):
            self._script = typing.cast(
                LibraScript, LibraUnknownScript(self._user_tx.script)
            )

    @property
    def sender(self) -> bytes:
        return bytes.fromhex(self._user_tx.sender)

    @property
    def sequence(self) -> int:
        return self._user_tx.sequence_number

    @property
    def max_gas_amount(self) -> int:
        return self._user_tx.max_gas_amount

    @property
    def gas_unit_price(self) -> int:
        return self._user_tx.gas_unit_price

    @property
    def gas_currency(self) -> str:
        return self._user_tx.gas_currency

    @property
    def expiration_timestamp_secs(self) -> int:
        return self._user_tx.expiration_timestamp_secs

    @property
    def public_key(self) -> bytes:
        return bytes.fromhex(self._user_tx.public_key)

    @property
    def signature(self) -> bytes:
        return bytes.fromhex(self._user_tx.signature)

    @property
    def script_hash(self) -> bytes:
        return bytes.fromhex(self._user_tx.script_hash)

    @property
    def script(self) -> LibraScript:
        return self._script

    @property
    def chain_id(self) -> int:
        return self._user_tx.chain_id


class LibraBlockMetadataTransaction(LibraTransaction):
    _block_metadata_tx: BlockMetadataTransactionData

    def __init__(self, transaction_resp: Transaction):
        super().__init__(transaction_resp)

        self._block_metadata_tx = typing.cast(
            BlockMetadataTransactionData, transaction_resp.transaction
        )

    @property
    def timestamp(self) -> int:
        return self._block_metadata_tx.timestamp_usecs


class LibraWriteSetTransaction(LibraTransaction):
    def __init__(self, transaction_resp: Transaction):
        super().__init__(transaction_resp)


class LibraUnknownTransaction(LibraTransaction):
    def __init__(self, transaction_resp: Transaction):
        super().__init__(transaction_resp)
