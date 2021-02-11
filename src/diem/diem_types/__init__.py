# pyre-strict
from dataclasses import dataclass
import typing
from diem import serde_types as st
from diem import bcs


@dataclass(frozen=True)
class AccessPath:
    address: "AccountAddress"
    path: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, AccessPath)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "AccessPath":
        v, buffer = bcs.deserialize(input, AccessPath)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
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

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, AccountAddress)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "AccountAddress":
        v, buffer = bcs.deserialize(input, AccountAddress)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    LENGTH = 16  # type: int

    def to_bytes(self) -> bytes:
        """Convert account address to bytes."""
        return bytes(typing.cast(typing.Iterable[int], self.value))

    @staticmethod
    def from_bytes(addr: bytes) -> "AccountAddress":
        """Create an account address from bytes."""
        if len(addr) != AccountAddress.LENGTH:
            raise ValueError("Incorrect length for an account address")
        return AccountAddress(value=tuple(st.uint8(x) for x in addr))  # pyre-ignore

    def to_hex(self) -> str:
        """Convert account address to an hexadecimal string."""
        return self.to_bytes().hex()

    @staticmethod
    def from_hex(addr: str) -> "AccountAddress":
        """Create an account address from an hexadecimal string."""
        return AccountAddress.from_bytes(bytes.fromhex(addr))


@dataclass(frozen=True)
class BlockMetadata:
    id: "HashValue"
    round: st.uint64
    timestamp_usecs: st.uint64
    previous_block_votes: typing.Sequence["AccountAddress"]
    proposer: "AccountAddress"

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, BlockMetadata)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "BlockMetadata":
        v, buffer = bcs.deserialize(input, BlockMetadata)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class ChainId:
    value: st.uint8

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, ChainId)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "ChainId":
        v, buffer = bcs.deserialize(input, ChainId)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def from_int(id: int) -> "ChainId":
        return ChainId(value=st.uint8(id))

    def to_int(self) -> int:
        return int(self.value)


@dataclass(frozen=True)
class ChangeSet:
    write_set: "WriteSet"
    events: typing.Sequence["ContractEvent"]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, ChangeSet)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "ChangeSet":
        v, buffer = bcs.deserialize(input, ChangeSet)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class CoinTradeMetadata:
    VARIANTS = []  # type: typing.Sequence[typing.Type[CoinTradeMetadata]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, CoinTradeMetadata)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "CoinTradeMetadata":
        v, buffer = bcs.deserialize(input, CoinTradeMetadata)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class CoinTradeMetadata__CoinTradeMetadataV0(CoinTradeMetadata):
    INDEX = 0  # type: int
    value: "CoinTradeMetadataV0"


CoinTradeMetadata.VARIANTS = [
    CoinTradeMetadata__CoinTradeMetadataV0,
]


@dataclass(frozen=True)
class CoinTradeMetadataV0:
    trade_ids: typing.Sequence[str]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, CoinTradeMetadataV0)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "CoinTradeMetadataV0":
        v, buffer = bcs.deserialize(input, CoinTradeMetadataV0)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class ContractEvent:
    VARIANTS = []  # type: typing.Sequence[typing.Type[ContractEvent]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, ContractEvent)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "ContractEvent":
        v, buffer = bcs.deserialize(input, ContractEvent)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class ContractEvent__V0(ContractEvent):
    INDEX = 0  # type: int
    value: "ContractEventV0"


ContractEvent.VARIANTS = [
    ContractEvent__V0,
]


@dataclass(frozen=True)
class ContractEventV0:
    key: "EventKey"
    sequence_number: st.uint64
    type_tag: "TypeTag"
    event_data: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, ContractEventV0)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "ContractEventV0":
        v, buffer = bcs.deserialize(input, ContractEventV0)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class Ed25519PublicKey:
    value: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, Ed25519PublicKey)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "Ed25519PublicKey":
        v, buffer = bcs.deserialize(input, Ed25519PublicKey)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class Ed25519Signature:
    value: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, Ed25519Signature)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "Ed25519Signature":
        v, buffer = bcs.deserialize(input, Ed25519Signature)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class EventKey:
    value: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, EventKey)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "EventKey":
        v, buffer = bcs.deserialize(input, EventKey)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class GeneralMetadata:
    VARIANTS = []  # type: typing.Sequence[typing.Type[GeneralMetadata]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, GeneralMetadata)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "GeneralMetadata":
        v, buffer = bcs.deserialize(input, GeneralMetadata)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class GeneralMetadata__GeneralMetadataVersion0(GeneralMetadata):
    INDEX = 0  # type: int
    value: "GeneralMetadataV0"


GeneralMetadata.VARIANTS = [
    GeneralMetadata__GeneralMetadataVersion0,
]


@dataclass(frozen=True)
class GeneralMetadataV0:
    to_subaddress: typing.Optional[bytes]
    from_subaddress: typing.Optional[bytes]
    referenced_event: typing.Optional[st.uint64]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, GeneralMetadataV0)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "GeneralMetadataV0":
        v, buffer = bcs.deserialize(input, GeneralMetadataV0)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class HashValue:
    value: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, HashValue)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "HashValue":
        v, buffer = bcs.deserialize(input, HashValue)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class Identifier:
    value: str

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, Identifier)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "Identifier":
        v, buffer = bcs.deserialize(input, Identifier)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class Metadata:
    VARIANTS = []  # type: typing.Sequence[typing.Type[Metadata]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, Metadata)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "Metadata":
        v, buffer = bcs.deserialize(input, Metadata)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    def decode_structure(self) -> typing.Union[None, "GeneralMetadataV0", "TravelRuleMetadataV0", "RefundMetadataV0"]:
        """decode metadata structure

        Returns None for a non-structure type or undefined
        """

        type_index = type(self).INDEX
        if type_index == 1:
            return typing.cast(GeneralMetadataV0, self.value.value)
        elif type_index == 2:
            return typing.cast(TravelRuleMetadataV0, self.value.value)
        elif type_index == 4:
            return typing.cast(RefundMetadataV0, self.value.value)
        elif type_index == 5:
            return typing.cast(CoinTradeMetadataV0, self.value.value)
        return None


@dataclass(frozen=True)
class Metadata__Undefined(Metadata):
    INDEX = 0  # type: int
    pass


@dataclass(frozen=True)
class Metadata__GeneralMetadata(Metadata):
    INDEX = 1  # type: int
    value: "GeneralMetadata"


@dataclass(frozen=True)
class Metadata__TravelRuleMetadata(Metadata):
    INDEX = 2  # type: int
    value: "TravelRuleMetadata"


@dataclass(frozen=True)
class Metadata__UnstructuredBytesMetadata(Metadata):
    INDEX = 3  # type: int
    value: "UnstructuredBytesMetadata"


@dataclass(frozen=True)
class Metadata__RefundMetadata(Metadata):
    INDEX = 4  # type: int
    value: "RefundMetadata"


@dataclass(frozen=True)
class Metadata__CoinTradeMetadata(Metadata):
    INDEX = 5  # type: int
    value: "CoinTradeMetadata"


Metadata.VARIANTS = [
    Metadata__Undefined,
    Metadata__GeneralMetadata,
    Metadata__TravelRuleMetadata,
    Metadata__UnstructuredBytesMetadata,
    Metadata__RefundMetadata,
    Metadata__CoinTradeMetadata,
]


@dataclass(frozen=True)
class Module:
    code: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, Module)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "Module":
        v, buffer = bcs.deserialize(input, Module)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class MultiEd25519PublicKey:
    value: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, MultiEd25519PublicKey)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "MultiEd25519PublicKey":
        v, buffer = bcs.deserialize(input, MultiEd25519PublicKey)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class MultiEd25519Signature:
    value: bytes

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, MultiEd25519Signature)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "MultiEd25519Signature":
        v, buffer = bcs.deserialize(input, MultiEd25519Signature)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class RawTransaction:
    sender: "AccountAddress"
    sequence_number: st.uint64
    payload: "TransactionPayload"
    max_gas_amount: st.uint64
    gas_unit_price: st.uint64
    gas_currency_code: str
    expiration_timestamp_secs: st.uint64
    chain_id: "ChainId"

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, RawTransaction)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "RawTransaction":
        v, buffer = bcs.deserialize(input, RawTransaction)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class RefundMetadata:
    VARIANTS = []  # type: typing.Sequence[typing.Type[RefundMetadata]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, RefundMetadata)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "RefundMetadata":
        v, buffer = bcs.deserialize(input, RefundMetadata)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class RefundMetadata__RefundMetadataV0(RefundMetadata):
    INDEX = 0  # type: int
    value: "RefundMetadataV0"


RefundMetadata.VARIANTS = [
    RefundMetadata__RefundMetadataV0,
]


@dataclass(frozen=True)
class RefundMetadataV0:
    transaction_version: st.uint64
    reason: "RefundReason"

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, RefundMetadataV0)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "RefundMetadataV0":
        v, buffer = bcs.deserialize(input, RefundMetadataV0)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class RefundReason:
    VARIANTS = []  # type: typing.Sequence[typing.Type[RefundReason]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, RefundReason)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "RefundReason":
        v, buffer = bcs.deserialize(input, RefundReason)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class RefundReason__OtherReason(RefundReason):
    INDEX = 0  # type: int
    pass


@dataclass(frozen=True)
class RefundReason__InvalidSubaddress(RefundReason):
    INDEX = 1  # type: int
    pass


@dataclass(frozen=True)
class RefundReason__UserInitiatedPartialRefund(RefundReason):
    INDEX = 2  # type: int
    pass


@dataclass(frozen=True)
class RefundReason__UserInitiatedFullRefund(RefundReason):
    INDEX = 3  # type: int
    pass


RefundReason.VARIANTS = [
    RefundReason__OtherReason,
    RefundReason__InvalidSubaddress,
    RefundReason__UserInitiatedPartialRefund,
    RefundReason__UserInitiatedFullRefund,
]


@dataclass(frozen=True)
class Script:
    code: bytes
    ty_args: typing.Sequence["TypeTag"]
    args: typing.Sequence["TransactionArgument"]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, Script)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "Script":
        v, buffer = bcs.deserialize(input, Script)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class SignedTransaction:
    raw_txn: "RawTransaction"
    authenticator: "TransactionAuthenticator"

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, SignedTransaction)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "SignedTransaction":
        v, buffer = bcs.deserialize(input, SignedTransaction)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    @staticmethod
    def from_raw_txn_and_ed25519_key(txn: RawTransaction, public_key: bytes, signature: bytes) -> "SignedTransaction":
        return SignedTransaction(
            raw_txn=txn,
            authenticator=TransactionAuthenticator__Ed25519(
                public_key=Ed25519PublicKey(value=public_key),
                signature=Ed25519Signature(value=signature),
            ),
        )


@dataclass(frozen=True)
class StructTag:
    address: "AccountAddress"
    module: "Identifier"
    name: "Identifier"
    type_params: typing.Sequence["TypeTag"]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, StructTag)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "StructTag":
        v, buffer = bcs.deserialize(input, StructTag)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class Transaction:
    VARIANTS = []  # type: typing.Sequence[typing.Type[Transaction]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, Transaction)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "Transaction":
        v, buffer = bcs.deserialize(input, Transaction)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class Transaction__UserTransaction(Transaction):
    INDEX = 0  # type: int
    value: "SignedTransaction"


@dataclass(frozen=True)
class Transaction__GenesisTransaction(Transaction):
    INDEX = 1  # type: int
    value: "WriteSetPayload"


@dataclass(frozen=True)
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

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, TransactionArgument)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "TransactionArgument":
        v, buffer = bcs.deserialize(input, TransactionArgument)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class TransactionArgument__U8(TransactionArgument):
    INDEX = 0  # type: int
    value: st.uint8


@dataclass(frozen=True)
class TransactionArgument__U64(TransactionArgument):
    INDEX = 1  # type: int
    value: st.uint64


@dataclass(frozen=True)
class TransactionArgument__U128(TransactionArgument):
    INDEX = 2  # type: int
    value: st.uint128


@dataclass(frozen=True)
class TransactionArgument__Address(TransactionArgument):
    INDEX = 3  # type: int
    value: "AccountAddress"


@dataclass(frozen=True)
class TransactionArgument__U8Vector(TransactionArgument):
    INDEX = 4  # type: int
    value: bytes


@dataclass(frozen=True)
class TransactionArgument__Bool(TransactionArgument):
    INDEX = 5  # type: int
    value: bool


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

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, TransactionAuthenticator)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "TransactionAuthenticator":
        v, buffer = bcs.deserialize(input, TransactionAuthenticator)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class TransactionAuthenticator__Ed25519(TransactionAuthenticator):
    INDEX = 0  # type: int
    public_key: "Ed25519PublicKey"
    signature: "Ed25519Signature"


@dataclass(frozen=True)
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

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, TransactionPayload)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "TransactionPayload":
        v, buffer = bcs.deserialize(input, TransactionPayload)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class TransactionPayload__WriteSet(TransactionPayload):
    INDEX = 0  # type: int
    value: "WriteSetPayload"


@dataclass(frozen=True)
class TransactionPayload__Script(TransactionPayload):
    INDEX = 1  # type: int
    value: "Script"


@dataclass(frozen=True)
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

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, TravelRuleMetadata)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "TravelRuleMetadata":
        v, buffer = bcs.deserialize(input, TravelRuleMetadata)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class TravelRuleMetadata__TravelRuleMetadataVersion0(TravelRuleMetadata):
    INDEX = 0  # type: int
    value: "TravelRuleMetadataV0"


TravelRuleMetadata.VARIANTS = [
    TravelRuleMetadata__TravelRuleMetadataVersion0,
]


@dataclass(frozen=True)
class TravelRuleMetadataV0:
    off_chain_reference_id: typing.Optional[str]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, TravelRuleMetadataV0)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "TravelRuleMetadataV0":
        v, buffer = bcs.deserialize(input, TravelRuleMetadataV0)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class TypeTag:
    VARIANTS = []  # type: typing.Sequence[typing.Type[TypeTag]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, TypeTag)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "TypeTag":
        v, buffer = bcs.deserialize(input, TypeTag)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v

    CORE_CODE_ADDRESS: AccountAddress = AccountAddress.from_hex("00000000000000000000000000000001")

    @staticmethod
    def from_currency_code(code: str) -> "TypeTag":
        if isinstance(code, str):
            return TypeTag__Struct(
                value=StructTag(
                    address=TypeTag.CORE_CODE_ADDRESS,
                    module=Identifier(code),
                    name=Identifier(code),
                    type_params=[],
                )
            )

        raise TypeError(f"unknown currency code type: {code}")

    def to_currency_code(self) -> str:
        if isinstance(self, TypeTag__Struct):
            return self.value.name.value

        raise TypeError(f"unknown currency code type: {self}")


@dataclass(frozen=True)
class TypeTag__Bool(TypeTag):
    INDEX = 0  # type: int
    pass


@dataclass(frozen=True)
class TypeTag__U8(TypeTag):
    INDEX = 1  # type: int
    pass


@dataclass(frozen=True)
class TypeTag__U64(TypeTag):
    INDEX = 2  # type: int
    pass


@dataclass(frozen=True)
class TypeTag__U128(TypeTag):
    INDEX = 3  # type: int
    pass


@dataclass(frozen=True)
class TypeTag__Address(TypeTag):
    INDEX = 4  # type: int
    pass


@dataclass(frozen=True)
class TypeTag__Signer(TypeTag):
    INDEX = 5  # type: int
    pass


@dataclass(frozen=True)
class TypeTag__Vector(TypeTag):
    INDEX = 6  # type: int
    value: "TypeTag"


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class UnstructuredBytesMetadata:
    metadata: typing.Optional[bytes]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, UnstructuredBytesMetadata)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "UnstructuredBytesMetadata":
        v, buffer = bcs.deserialize(input, UnstructuredBytesMetadata)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class WriteOp:
    VARIANTS = []  # type: typing.Sequence[typing.Type[WriteOp]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, WriteOp)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "WriteOp":
        v, buffer = bcs.deserialize(input, WriteOp)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class WriteOp__Deletion(WriteOp):
    INDEX = 0  # type: int
    pass


@dataclass(frozen=True)
class WriteOp__Value(WriteOp):
    INDEX = 1  # type: int
    value: bytes


WriteOp.VARIANTS = [
    WriteOp__Deletion,
    WriteOp__Value,
]


@dataclass(frozen=True)
class WriteSet:
    value: "WriteSetMut"

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, WriteSet)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "WriteSet":
        v, buffer = bcs.deserialize(input, WriteSet)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class WriteSetMut:
    write_set: typing.Sequence[typing.Tuple["AccessPath", "WriteOp"]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, WriteSetMut)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "WriteSetMut":
        v, buffer = bcs.deserialize(input, WriteSetMut)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


class WriteSetPayload:
    VARIANTS = []  # type: typing.Sequence[typing.Type[WriteSetPayload]]

    def bcs_serialize(self) -> bytes:
        return bcs.serialize(self, WriteSetPayload)

    @staticmethod
    def bcs_deserialize(input: bytes) -> "WriteSetPayload":
        v, buffer = bcs.deserialize(input, WriteSetPayload)
        if buffer:
            raise st.DeserializationError("Some input bytes were not read")
        return v


@dataclass(frozen=True)
class WriteSetPayload__Direct(WriteSetPayload):
    INDEX = 0  # type: int
    value: "ChangeSet"


@dataclass(frozen=True)
class WriteSetPayload__Script(WriteSetPayload):
    INDEX = 1  # type: int
    execute_as: "AccountAddress"
    script: "Script"


WriteSetPayload.VARIANTS = [
    WriteSetPayload__Direct,
    WriteSetPayload__Script,
]
