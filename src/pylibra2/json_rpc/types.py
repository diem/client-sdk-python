import typing
from dataclasses import dataclass, field, fields


@dataclass
class JsonRpcError:
    code: int
    data: typing.Optional[typing.Dict[str, str]]
    message: str


@dataclass
class Amount:
    amount: int
    currency: str


@dataclass
class ParentVASPRole:
    human_name: str
    base_url: str
    expiration_time: int
    compliance_key: str
    num_children: int
    base_url_rotation_events_key: str
    compliance_key_rotation_events_key: str
    type: str = "parent_vasp"


@dataclass
class ChildVASPRole:
    parent_vasp_address: str
    type: str = "child_vasp"


@dataclass
class DesignatedDealerRole:
    human_name: str
    base_url: str
    expiration_time: int
    compliance_key: str
    preburn_balance: typing.List[Amount]
    received_mint_events_key: str
    base_url_rotation_events_key: str
    compliance_key_rotation_events_key: str
    type: str = "designated_dealer"


@dataclass
class UnknownRole:
    type: str = "unknown"


Role = typing.Union[ParentVASPRole, ChildVASPRole, DesignatedDealerRole, UnknownRole]


@dataclass
class CurrencyInfo:
    code: str
    fractional_part: int
    scaling_factor: int
    to_lbr_exchange_rate: float
    mint_events_key: str
    burn_events_key: str
    preburn_events_key: str
    cancel_burn_events_key: str
    exchange_rate_update_events_key: str


@dataclass
class PeerToPeerTransactionScript:
    receiver: str
    amount: int
    currency: str
    metadata: str
    metadata_signature: str
    type: str = "peer_to_peer_transaction"


@dataclass
class MintTransactionScript:
    receiver: str
    auth_key_prefix: str
    amount: int
    type: str = "mint_transaction"


@dataclass
class UnknownTransactionScript:
    type: str = "unknown"


Script = typing.Union[
    PeerToPeerTransactionScript, MintTransactionScript, UnknownTransactionScript
]


@dataclass
class UserTransactionData:
    chain_id: int
    sender: str
    signature_scheme: str
    signature: str
    public_key: str
    sequence_number: int
    max_gas_amount: int
    gas_unit_price: int
    gas_currency: str
    expiration_timestamp_secs: int
    script_hash: str
    script_bytes: str
    script: Script
    type: str = "user"


@dataclass
class BlockMetadataTransactionData:
    timestamp_usecs: int
    type: str = "blockmetadata"


@dataclass
class WriteSetTransactionData:
    type: str = "writeset"


@dataclass
class UnknownTransactionData:
    type: str = "unknown"


TransactionData = typing.Union[
    UserTransactionData,
    BlockMetadataTransactionData,
    WriteSetTransactionData,
    UnknownTransactionData,
]


@dataclass
class BurnEventData:
    amount: Amount
    preburn_address: str
    type: str = "burn"


@dataclass
class CancelBurnEventData:
    amount: Amount
    preburn_address: str
    type: str = "cancelburn"


@dataclass
class PreBurnEventData:
    amount: Amount
    preburn_address: str
    type: str = "preburn"


@dataclass
class MintEventData:
    amount: Amount
    type: str = "mint"


@dataclass
class ToLbrExchangeRateUpdateEventData:
    currency_code: str
    new_to_lbr_exchange_rate: float
    type: str = "to_lbr_exchange_rate_update"


@dataclass
class ReceivedPaymentEventData:
    amount: Amount
    sender: str
    receiver: str
    metadata: str
    type: str = "receivedpayment"


@dataclass
class SentPaymentEventData:
    amount: Amount
    sender: str
    receiver: str
    metadata: str
    type: str = "sentpayment"


@dataclass
class UnknownEventData:
    type: str = "unknown"


# TODO (T72118696): add latest libra types, e.g. 'newblock' https://fburl.com/5tb45n3t
EventData = typing.Union[
    BurnEventData,
    CancelBurnEventData,
    PreBurnEventData,
    MintEventData,
    ToLbrExchangeRateUpdateEventData,
    ReceivedPaymentEventData,
    SentPaymentEventData,
    UnknownEventData,
]


@dataclass
class Event:
    key: str
    sequence_number: int
    transaction_version: int
    data: EventData


@dataclass
class AccountStateResponse:
    address: str
    balances: typing.List[Amount]
    sequence_number: int
    authentication_key: str
    sent_events_key: str
    received_events_key: str
    delegated_key_rotation_capability: bool
    delegated_withdrawal_capability: bool
    is_frozen: bool
    role: Role


@dataclass
class MetadataResponse:
    version: int
    timestamp: int


@dataclass
class CurrencyResponse:
    currencies_info: typing.List[CurrencyInfo] = field(default_factory=list)


@dataclass
class ExecutedVMStatus:
    type: str = "executed"


@dataclass
class OutOfGasVMStatus:
    type: str = "out_of_gas"


@dataclass
class MoveAbortVMStatus:
    location: str
    abort_code: int
    type: str = "move_abort"


@dataclass
class ExecutionFailureVMStatus:
    location: str
    function_index: int
    code_offset: int
    type: str = "execution_failure"


@dataclass
class VerificationErrorVMStatus:
    type: str = "verification_error"


@dataclass
class DeserializationErrorVMStatus:
    type: str = "deserialization_error"


@dataclass
class PublishingFailureVMStatus:
    type: str = "publishing_failure"


@dataclass
class UnknownVMStatus:
    type: str = "unknown"


VMStatus = typing.Union[
    ExecutedVMStatus,
    OutOfGasVMStatus,
    MoveAbortVMStatus,
    ExecutionFailureVMStatus,
    VerificationErrorVMStatus,
    DeserializationErrorVMStatus,
    PublishingFailureVMStatus,
    UnknownVMStatus,
]


@dataclass
class Transaction:
    transaction: TransactionData
    events: typing.List[Event]
    version: int
    vm_status: VMStatus
    gas_used: int
    hash: str
    bytes: str


UNION_TYPES = (EventData, Role, Script, TransactionData, VMStatus)


def f_create_union_type(
    union: typing.Type,
    f_create: typing.Callable[[typing.Type, typing.Dict[str, typing.Any]], typing.Any],
) -> typing.Callable[..., typing.Type]:
    type_map = {_type.type: _type for _type in union.__args__}

    def normalize_data(
        data_: typing.Union[str, typing.Dict[str, typing.Any]]
    ) -> typing.Dict[str, typing.Any]:
        norm_data: typing.Dict[str, typing.Any] = {}
        if isinstance(data_, str):
            norm_data.update(type=data_)
        elif isinstance(data_, dict):
            if "type" not in data_:
                keys, values = (list(li) for li in (data_.keys(), data_.values()))
                if len(keys) == 1 and isinstance(values[0], dict):
                    norm_data.update(type=keys[0], **typing.cast(dict, values[0]))
            else:
                norm_data.update(data_)

        return norm_data

    def create(data_: typing.Union[str, typing.Dict[str, typing.Any]]) -> typing.Any:
        """ Create a class instance from a json-rpc response object. Interprets 'type'
            from both new/old style server responses. Uses type 'unknown' if type isn't supported

            Args:
                data: either a string specifying 'type_value' (old style)
                      OR a dict containing {'type_value': attr_dict} (old style)
                      OR an attr_dict containing {'type': 'type_value'} (new style)

            Returns:
                An instantiated class that is a member of the passed type Union
        """
        norm_data = normalize_data(data_)
        if "type" not in norm_data or norm_data["type"] not in type_map:
            norm_data = {"type": "unknown"}

        _type = type_map[norm_data["type"]]
        for _field in fields(_type):
            if _field.type in UNION_TYPES:
                norm_data[_field.name] = normalize_data(norm_data[_field.name])

        return f_create(_type, norm_data)

    return create
