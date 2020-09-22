# pyre-strict
import typing
from dataclasses import dataclass

from .. import lcs, serde_types as st


@dataclass
class AccessPath:
    address: "AccountAddress"
    path: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, AccessPath)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "AccessPath":
        v, buffer = lcs.deserialize(input, AccessPath)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


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

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, AccountAddress)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "AccountAddress":
        v, buffer = lcs.deserialize(input, AccountAddress)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class BlockMetadata:
    id: "HashValue"
    round: st.uint64
    timestamp_usecs: st.uint64
    previous_block_votes: typing.Sequence["AccountAddress"]
    proposer: "AccountAddress"

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, BlockMetadata)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "BlockMetadata":
        v, buffer = lcs.deserialize(input, BlockMetadata)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class ChainId:
    value: st.uint8

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, ChainId)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "ChainId":
        v, buffer = lcs.deserialize(input, ChainId)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class ChangeSet:
    write_set: "WriteSet"
    events: typing.Sequence["ContractEvent"]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, ChangeSet)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "ChangeSet":
        v, buffer = lcs.deserialize(input, ChangeSet)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


class ContractEvent:
    VARIANTS = []  # type: typing.Sequence[typing.Type[ContractEvent]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, ContractEvent)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "ContractEvent":
        v, buffer = lcs.deserialize(input, ContractEvent)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class ContractEvent__V0(ContractEvent):
    INDEX = 0  # type: int
    value: "ContractEventV0"


ContractEvent.VARIANTS = [ContractEvent__V0]


@dataclass
class ContractEventV0:
    key: "EventKey"
    sequence_number: st.uint64
    type_tag: "TypeTag"
    event_data: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, ContractEventV0)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "ContractEventV0":
        v, buffer = lcs.deserialize(input, ContractEventV0)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class Ed25519PublicKey:
    value: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, Ed25519PublicKey)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "Ed25519PublicKey":
        v, buffer = lcs.deserialize(input, Ed25519PublicKey)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class Ed25519Signature:
    value: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, Ed25519Signature)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "Ed25519Signature":
        v, buffer = lcs.deserialize(input, Ed25519Signature)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class EventKey:
    value: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, EventKey)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "EventKey":
        v, buffer = lcs.deserialize(input, EventKey)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


class GeneralMetadata:
    VARIANTS = []  # type: typing.Sequence[typing.Type[GeneralMetadata]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, GeneralMetadata)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "GeneralMetadata":
        v, buffer = lcs.deserialize(input, GeneralMetadata)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class GeneralMetadata__GeneralMetadataVersion0(GeneralMetadata):
    INDEX = 0  # type: int
    value: "GeneralMetadataV0"


GeneralMetadata.VARIANTS = [GeneralMetadata__GeneralMetadataVersion0]


@dataclass
class GeneralMetadataV0:
    to_subaddress: typing.Optional[bytes]
    from_subaddress: typing.Optional[bytes]
    referenced_event: typing.Optional[st.uint64]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, GeneralMetadataV0)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "GeneralMetadataV0":
        v, buffer = lcs.deserialize(input, GeneralMetadataV0)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class HashValue:
    value: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, HashValue)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "HashValue":
        v, buffer = lcs.deserialize(input, HashValue)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class Identifier:
    value: str

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, Identifier)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "Identifier":
        v, buffer = lcs.deserialize(input, Identifier)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


class Metadata:
    VARIANTS = []  # type: typing.Sequence[typing.Type[Metadata]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, Metadata)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "Metadata":
        v, buffer = lcs.deserialize(input, Metadata)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class Metadata__Undefined(Metadata):
    INDEX = 0  # type: int
    pass


@dataclass
class Metadata__GeneralMetadata(Metadata):
    INDEX = 1  # type: int
    value: "GeneralMetadata"


@dataclass
class Metadata__TravelRuleMetadata(Metadata):
    INDEX = 2  # type: int
    value: "TravelRuleMetadata"


@dataclass
class Metadata__UnstructuredBytesMetadata(Metadata):
    INDEX = 3  # type: int
    value: "UnstructuredBytesMetadata"


Metadata.VARIANTS = [
    Metadata__Undefined,
    Metadata__GeneralMetadata,
    Metadata__TravelRuleMetadata,
    Metadata__UnstructuredBytesMetadata,
]


@dataclass
class Module:
    code: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, Module)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "Module":
        v, buffer = lcs.deserialize(input, Module)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class MultiEd25519PublicKey:
    value: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, MultiEd25519PublicKey)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "MultiEd25519PublicKey":
        v, buffer = lcs.deserialize(input, MultiEd25519PublicKey)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class MultiEd25519Signature:
    value: bytes

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, MultiEd25519Signature)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "MultiEd25519Signature":
        v, buffer = lcs.deserialize(input, MultiEd25519Signature)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class RawTransaction:
    sender: "AccountAddress"
    sequence_number: st.uint64
    payload: "TransactionPayload"
    max_gas_amount: st.uint64
    gas_unit_price: st.uint64
    gas_currency_code: str
    expiration_timestamp_secs: st.uint64
    chain_id: "ChainId"

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, RawTransaction)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "RawTransaction":
        v, buffer = lcs.deserialize(input, RawTransaction)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class Script:
    code: bytes
    ty_args: typing.Sequence["TypeTag"]
    args: typing.Sequence["TransactionArgument"]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, Script)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "Script":
        v, buffer = lcs.deserialize(input, Script)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class SignedTransaction:
    raw_txn: "RawTransaction"
    authenticator: "TransactionAuthenticator"

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, SignedTransaction)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "SignedTransaction":
        v, buffer = lcs.deserialize(input, SignedTransaction)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class StructTag:
    address: "AccountAddress"
    module: "Identifier"
    name: "Identifier"
    type_params: typing.Sequence["TypeTag"]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, StructTag)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "StructTag":
        v, buffer = lcs.deserialize(input, StructTag)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


class Transaction:
    VARIANTS = []  # type: typing.Sequence[typing.Type[Transaction]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, Transaction)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "Transaction":
        v, buffer = lcs.deserialize(input, Transaction)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class Transaction__UserTransaction(Transaction):
    INDEX = 0  # type: int
    value: "SignedTransaction"


@dataclass
class Transaction__GenesisTransaction(Transaction):
    INDEX = 1  # type: int
    value: "WriteSetPayload"


@dataclass
class Transaction__BlockMetadata(Transaction):
    INDEX = 2  # type: int
    value: "BlockMetadata"


Transaction.VARIANTS = [
    Transaction__UserTransaction,
    Transaction__GenesisTransaction,
    Transaction__BlockMetadata,
]


class TransactionArgument:
    VARIANTS = []  # type: typing.Sequence[typing.Type[TransactionArgument]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, TransactionArgument)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "TransactionArgument":
        v, buffer = lcs.deserialize(input, TransactionArgument)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class TransactionArgument__U8(TransactionArgument):
    INDEX = 0  # type: int
    value: st.uint8


@dataclass
class TransactionArgument__U64(TransactionArgument):
    INDEX = 1  # type: int
    value: st.uint64


@dataclass
class TransactionArgument__U128(TransactionArgument):
    INDEX = 2  # type: int
    value: st.uint128


@dataclass
class TransactionArgument__Address(TransactionArgument):
    INDEX = 3  # type: int
    value: "AccountAddress"


@dataclass
class TransactionArgument__U8Vector(TransactionArgument):
    INDEX = 4  # type: int
    value: bytes


@dataclass
class TransactionArgument__Bool(TransactionArgument):
    INDEX = 5  # type: int
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
    VARIANTS = []  # type: typing.Sequence[typing.Type[TransactionAuthenticator]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, TransactionAuthenticator)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "TransactionAuthenticator":
        v, buffer = lcs.deserialize(input, TransactionAuthenticator)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class TransactionAuthenticator__Ed25519(TransactionAuthenticator):
    INDEX = 0  # type: int
    public_key: "Ed25519PublicKey"
    signature: "Ed25519Signature"


@dataclass
class TransactionAuthenticator__MultiEd25519(TransactionAuthenticator):
    INDEX = 1  # type: int
    public_key: "MultiEd25519PublicKey"
    signature: "MultiEd25519Signature"


TransactionAuthenticator.VARIANTS = [
    TransactionAuthenticator__Ed25519,
    TransactionAuthenticator__MultiEd25519,
]


class TransactionPayload:
    VARIANTS = []  # type: typing.Sequence[typing.Type[TransactionPayload]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, TransactionPayload)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "TransactionPayload":
        v, buffer = lcs.deserialize(input, TransactionPayload)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class TransactionPayload__WriteSet(TransactionPayload):
    INDEX = 0  # type: int
    value: "WriteSetPayload"


@dataclass
class TransactionPayload__Script(TransactionPayload):
    INDEX = 1  # type: int
    value: "Script"


@dataclass
class TransactionPayload__Module(TransactionPayload):
    INDEX = 2  # type: int
    value: "Module"


TransactionPayload.VARIANTS = [
    TransactionPayload__WriteSet,
    TransactionPayload__Script,
    TransactionPayload__Module,
]


class TravelRuleMetadata:
    VARIANTS = []  # type: typing.Sequence[typing.Type[TravelRuleMetadata]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, TravelRuleMetadata)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "TravelRuleMetadata":
        v, buffer = lcs.deserialize(input, TravelRuleMetadata)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class TravelRuleMetadata__TravelRuleMetadataVersion0(TravelRuleMetadata):
    INDEX = 0  # type: int
    value: "TravelRuleMetadataV0"


TravelRuleMetadata.VARIANTS = [TravelRuleMetadata__TravelRuleMetadataVersion0]


@dataclass
class TravelRuleMetadataV0:
    off_chain_reference_id: typing.Optional[str]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, TravelRuleMetadataV0)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "TravelRuleMetadataV0":
        v, buffer = lcs.deserialize(input, TravelRuleMetadataV0)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


class TypeTag:
    VARIANTS = []  # type: typing.Sequence[typing.Type[TypeTag]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, TypeTag)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "TypeTag":
        v, buffer = lcs.deserialize(input, TypeTag)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class TypeTag__Bool(TypeTag):
    INDEX = 0  # type: int
    pass


@dataclass
class TypeTag__U8(TypeTag):
    INDEX = 1  # type: int
    pass


@dataclass
class TypeTag__U64(TypeTag):
    INDEX = 2  # type: int
    pass


@dataclass
class TypeTag__U128(TypeTag):
    INDEX = 3  # type: int
    pass


@dataclass
class TypeTag__Address(TypeTag):
    INDEX = 4  # type: int
    pass


@dataclass
class TypeTag__Signer(TypeTag):
    INDEX = 5  # type: int
    pass


@dataclass
class TypeTag__Vector(TypeTag):
    INDEX = 6  # type: int
    value: "TypeTag"


@dataclass
class TypeTag__Struct(TypeTag):
    INDEX = 7  # type: int
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


@dataclass
class UnstructuredBytesMetadata:
    metadata: typing.Optional[bytes]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, UnstructuredBytesMetadata)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "UnstructuredBytesMetadata":
        v, buffer = lcs.deserialize(input, UnstructuredBytesMetadata)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


class WriteOp:
    VARIANTS = []  # type: typing.Sequence[typing.Type[WriteOp]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, WriteOp)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "WriteOp":
        v, buffer = lcs.deserialize(input, WriteOp)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class WriteOp__Deletion(WriteOp):
    INDEX = 0  # type: int
    pass


@dataclass
class WriteOp__Value(WriteOp):
    INDEX = 1  # type: int
    value: bytes


WriteOp.VARIANTS = [WriteOp__Deletion, WriteOp__Value]


@dataclass
class WriteSet:
    value: "WriteSetMut"

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, WriteSet)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "WriteSet":
        v, buffer = lcs.deserialize(input, WriteSet)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class WriteSetMut:
    write_set: typing.Sequence[typing.Tuple["AccessPath", "WriteOp"]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, WriteSetMut)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "WriteSetMut":
        v, buffer = lcs.deserialize(input, WriteSetMut)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


class WriteSetPayload:
    VARIANTS = []  # type: typing.Sequence[typing.Type[WriteSetPayload]]

    def lcs_serialize(self) -> bytes:
        return lcs.serialize(self, WriteSetPayload)

    @staticmethod
    def lcs_deserialize(input: bytes) -> "WriteSetPayload":
        v, buffer = lcs.deserialize(input, WriteSetPayload)
        if buffer:
            raise ValueError("Some input bytes were not read")
        return v


@dataclass
class WriteSetPayload__Direct(WriteSetPayload):
    INDEX = 0  # type: int
    value: "ChangeSet"


@dataclass
class WriteSetPayload__Script(WriteSetPayload):
    INDEX = 1  # type: int
    execute_as: "AccountAddress"
    script: "Script"


WriteSetPayload.VARIANTS = [WriteSetPayload__Direct, WriteSetPayload__Script]
