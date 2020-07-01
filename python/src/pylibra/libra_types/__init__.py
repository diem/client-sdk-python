from dataclasses import dataclass
import typing
from pylibra import serde_types as st


@dataclass
class AccessPath:
    address: "AccountAddress"
    path: typing.Sequence[st.uint8]


@dataclass
class AccountAddress:
    value: typing.Tuple[
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
        st.uint8,
    ]


@dataclass
class BlockMetadata:
    id: "HashValue"
    round: st.uint64
    timestamp_usecs: st.uint64
    previous_block_votes: typing.Sequence["AccountAddress"]
    proposer: "AccountAddress"


@dataclass
class ChangeSet:
    write_set: "WriteSet"
    events: typing.Sequence["ContractEvent"]


class ContractEvent:
    VARIANTS = []


@dataclass
class ContractEvent__V0(ContractEvent):
    INDEX = 0
    value: "ContractEventV0"


ContractEvent.VARIANTS = [
    ContractEvent__V0,
]


@dataclass
class ContractEventV0:
    key: "EventKey"
    sequence_number: st.uint64
    type_tag: "TypeTag"
    event_data: typing.Sequence[st.uint8]


@dataclass
class Ed25519PublicKey:
    value: bytes


@dataclass
class Ed25519Signature:
    value: bytes


@dataclass
class EventKey:
    value: bytes


@dataclass
class HashValue:
    value: bytes


@dataclass
class Identifier:
    value: str


@dataclass
class Module:
    code: typing.Sequence[st.uint8]


@dataclass
class MultiEd25519PublicKey:
    value: bytes


@dataclass
class MultiEd25519Signature:
    value: bytes


@dataclass
class RawTransaction:
    sender: "AccountAddress"
    sequence_number: st.uint64
    payload: "TransactionPayload"
    max_gas_amount: st.uint64
    gas_unit_price: st.uint64
    gas_currency_code: str
    expiration_time: st.uint64


@dataclass
class Script:
    code: typing.Sequence[st.uint8]
    ty_args: typing.Sequence["TypeTag"]
    args: typing.Sequence["TransactionArgument"]


@dataclass
class SignedTransaction:
    raw_txn: "RawTransaction"
    authenticator: "TransactionAuthenticator"


@dataclass
class StructTag:
    address: "AccountAddress"
    module: "Identifier"
    name: "Identifier"
    type_params: typing.Sequence["TypeTag"]


class Transaction:
    VARIANTS = []


@dataclass
class Transaction__UserTransaction(Transaction):
    INDEX = 0
    value: "SignedTransaction"


@dataclass
class Transaction__WaypointWriteSet(Transaction):
    INDEX = 1
    value: "ChangeSet"


@dataclass
class Transaction__BlockMetadata(Transaction):
    INDEX = 2
    value: "BlockMetadata"


Transaction.VARIANTS = [
    Transaction__UserTransaction,
    Transaction__WaypointWriteSet,
    Transaction__BlockMetadata,
]


class TransactionArgument:
    VARIANTS = []


@dataclass
class TransactionArgument__U8(TransactionArgument):
    INDEX = 0
    value: st.uint8


@dataclass
class TransactionArgument__U64(TransactionArgument):
    INDEX = 1
    value: st.uint64


@dataclass
class TransactionArgument__U128(TransactionArgument):
    INDEX = 2
    value: st.uint128


@dataclass
class TransactionArgument__Address(TransactionArgument):
    INDEX = 3
    value: "AccountAddress"


@dataclass
class TransactionArgument__U8Vector(TransactionArgument):
    INDEX = 4
    value: typing.Sequence[st.uint8]


@dataclass
class TransactionArgument__Bool(TransactionArgument):
    INDEX = 5
    value: st.bool


TransactionArgument.VARIANTS = [
    TransactionArgument__U8,
    TransactionArgument__U64,
    TransactionArgument__U128,
    TransactionArgument__Address,
    TransactionArgument__U8Vector,
    TransactionArgument__Bool,
]


class TransactionAuthenticator:
    VARIANTS = []


@dataclass
class TransactionAuthenticator__Ed25519(TransactionAuthenticator):
    INDEX = 0
    public_key: "Ed25519PublicKey"
    signature: "Ed25519Signature"


@dataclass
class TransactionAuthenticator__MultiEd25519(TransactionAuthenticator):
    INDEX = 1
    public_key: "MultiEd25519PublicKey"
    signature: "MultiEd25519Signature"


TransactionAuthenticator.VARIANTS = [
    TransactionAuthenticator__Ed25519,
    TransactionAuthenticator__MultiEd25519,
]


class TransactionPayload:
    VARIANTS = []


@dataclass
class TransactionPayload__WriteSet(TransactionPayload):
    INDEX = 0
    value: "ChangeSet"


@dataclass
class TransactionPayload__Script(TransactionPayload):
    INDEX = 1
    value: "Script"


@dataclass
class TransactionPayload__Module(TransactionPayload):
    INDEX = 2
    value: "Module"


TransactionPayload.VARIANTS = [
    TransactionPayload__WriteSet,
    TransactionPayload__Script,
    TransactionPayload__Module,
]


class TypeTag:
    VARIANTS = []


@dataclass
class TypeTag__Bool(TypeTag):
    INDEX = 0


@dataclass
class TypeTag__U8(TypeTag):
    INDEX = 1


@dataclass
class TypeTag__U64(TypeTag):
    INDEX = 2


@dataclass
class TypeTag__U128(TypeTag):
    INDEX = 3


@dataclass
class TypeTag__Address(TypeTag):
    INDEX = 4


@dataclass
class TypeTag__Signer(TypeTag):
    INDEX = 5


@dataclass
class TypeTag__Vector(TypeTag):
    INDEX = 6
    value: "TypeTag"


@dataclass
class TypeTag__Struct(TypeTag):
    INDEX = 7
    value: "StructTag"


TypeTag.VARIANTS = [
    TypeTag__Bool,
    TypeTag__U8,
    TypeTag__U64,
    TypeTag__U128,
    TypeTag__Address,
    TypeTag__Signer,
    TypeTag__Vector,
    TypeTag__Struct,
]


class WriteOp:
    VARIANTS = []


@dataclass
class WriteOp__Deletion(WriteOp):
    INDEX = 0


@dataclass
class WriteOp__Value(WriteOp):
    INDEX = 1
    value: typing.Sequence[st.uint8]


WriteOp.VARIANTS = [
    WriteOp__Deletion,
    WriteOp__Value,
]


@dataclass
class WriteSet:
    value: "WriteSetMut"


@dataclass
class WriteSetMut:
    write_set: typing.Sequence[typing.Tuple["AccessPath", "WriteOp"]]
