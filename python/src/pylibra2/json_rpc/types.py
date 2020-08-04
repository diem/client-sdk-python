import typing
from dataclasses import dataclass, field


@dataclass
class JsonRpcError:
    code: int
    data: typing.Optional[typing.Dict[str, str]]
    message: str


@dataclass
class AmountData:
    amount: int
    currency: str


@dataclass
class ParentVASP:
    human_name: str
    base_url: str
    expiration_time: int
    compliance_key: str
    num_children: int


@dataclass
class ChildVASP:
    parent_vasp_address: str


@dataclass
class CurrencyInfo:
    code: str
    fractional_part: int
    scaling_factor: int


# All Scripts
@dataclass
class PeerToPeerTransferScript:
    type: str
    receiver: str
    auth_key_prefix: str
    amount: int
    metadata: str
    metadata_signature: str


@dataclass
class MintScript:
    type: str
    receiver: str
    auth_key_prefix: str
    amount: int


@dataclass
class UnknownScript:
    type: str


# All Transactions
@dataclass
class UserTransaction:
    type: str
    sender: str
    signature_scheme: str
    signature: str
    public_key: str
    sequence_number: int
    max_gas_amount: int
    gas_unit_price: int
    gas_currency: str
    expiration_time: int
    script_hash: str
    script: typing.Union[PeerToPeerTransferScript, MintScript, UnknownScript]


@dataclass
class BlockMetadataTransaction:
    type: str
    timestamp_usecs: int


@dataclass
class WriteSetTransaction:
    type: str


@dataclass
class UnknownTransaction:
    type: str


# All events
@dataclass
class ReceivedPaymentEvent:
    type: str
    amount: AmountData
    sender: str
    metadata: str


@dataclass
class SentPaymentEvent:
    type: str
    amount: AmountData
    receiver: str
    metadata: str


@dataclass
class UnknownEvent:
    type: str


@dataclass
class Event:
    key: str
    sequence_number: int
    transaction_version: int
    data: typing.Union[ReceivedPaymentEvent, SentPaymentEvent, UnknownEvent]


# All Responses
@dataclass
class AccountStateResponse:
    balances: typing.List[AmountData]
    sequence_number: int
    authentication_key: str
    sent_events_key: str
    received_events_key: str
    delegated_key_rotation_capability: bool
    delegated_withdrawal_capability: bool
    is_frozen: bool
    role: typing.Union[str, typing.Dict[str, typing.Union[ParentVASP, ChildVASP]]]


@dataclass
class MetadataResponse:
    version: int
    timestamp: int


@dataclass
class CurrencyResponse:
    currencies_info: typing.List[CurrencyInfo] = field(default_factory=list)


@dataclass
class TransactionResponse:
    transaction: typing.Union[
        UserTransaction,
        BlockMetadataTransaction,
        WriteSetTransaction,
        UnknownTransaction,
    ]
    events: typing.List[Event]
    version: int
    vm_status: int
    gas_used: int

    # Hack to create appropriate object of transaction if it is WriteSet/Unknown
    # dacite will instantiate either WriteSetTransaction/UnknownTransaction as it just matches attribute name/type which is same on both
    def __post_init__(self):
        if isinstance(self.transaction, WriteSetTransaction) or isinstance(
            self.transaction, UnknownTransaction
        ):
            if self.transaction.type == "writeset":
                self.transaction = WriteSetTransaction(type="writeset")
            elif self.transaction.type == "unknown":
                self.transaction = UnknownTransaction(type="unknown")
