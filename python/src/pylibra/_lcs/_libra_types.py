# pyre-ignore-all-errors

from dataclasses import dataclass
import numpy as np
import typing



@dataclass
class AccessPath:
    address: 'AccountAddress'
    path: typing.Sequence[np.uint8]

@dataclass
class AccountAddress:
    value: typing.Tuple[np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8, np.uint8]

@dataclass
class BlockMetadata:
    id: 'HashValue'
    round: np.uint64
    timestamp_usecs: np.uint64
    previous_block_votes: typing.Sequence['AccountAddress']
    proposer: 'AccountAddress'

@dataclass
class ChangeSet:
    write_set: 'WriteSet'
    events: typing.Sequence['ContractEvent']

class ContractEvent:
    pass

@dataclass
class _ContractEvent_V0(ContractEvent):
    INDEX=0
    value: 'ContractEventV0'


ContractEvent.V0 = _ContractEvent_V0
ContractEvent.VARIANTS = [ContractEvent.V0]

@dataclass
class ContractEventV0:
    key: 'EventKey'
    sequence_number: np.uint64
    type_tag: 'TypeTag'
    event_data: typing.Sequence[np.uint8]

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
    code: typing.Sequence[np.uint8]

@dataclass
class MultiEd25519PublicKey:
    value: bytes

@dataclass
class MultiEd25519Signature:
    value: bytes

@dataclass
class RawTransaction:
    sender: 'AccountAddress'
    sequence_number: np.uint64
    payload: 'TransactionPayload'
    max_gas_amount: np.uint64
    gas_unit_price: np.uint64
    gas_currency_code: str
    expiration_time: np.uint64

@dataclass
class Script:
    code: typing.Sequence[np.uint8]
    ty_args: typing.Sequence['TypeTag']
    args: typing.Sequence['TransactionArgument']

@dataclass
class SignedTransaction:
    raw_txn: 'RawTransaction'
    authenticator: 'TransactionAuthenticator'

@dataclass
class StructTag:
    address: 'AccountAddress'
    module: 'Identifier'
    name: 'Identifier'
    type_params: typing.Sequence['TypeTag']

class Transaction:
    pass

@dataclass
class _Transaction_UserTransaction(Transaction):
    INDEX=0
    value: 'SignedTransaction'


@dataclass
class _Transaction_WaypointWriteSet(Transaction):
    INDEX=1
    value: 'ChangeSet'


@dataclass
class _Transaction_BlockMetadata(Transaction):
    INDEX=2
    value: 'BlockMetadata'


Transaction.UserTransaction = _Transaction_UserTransaction
Transaction.WaypointWriteSet = _Transaction_WaypointWriteSet
Transaction.BlockMetadata = _Transaction_BlockMetadata
Transaction.VARIANTS = [Transaction.UserTransaction, Transaction.WaypointWriteSet, Transaction.BlockMetadata]

class TransactionArgument:
    pass

@dataclass
class _TransactionArgument_U8(TransactionArgument):
    INDEX=0
    value: np.uint8


@dataclass
class _TransactionArgument_U64(TransactionArgument):
    INDEX=1
    value: np.uint64


@dataclass
class _TransactionArgument_U128(TransactionArgument):
    INDEX=2
    value: typing.Tuple[np.uint64, np.uint64]


@dataclass
class _TransactionArgument_Address(TransactionArgument):
    INDEX=3
    value: 'AccountAddress'


@dataclass
class _TransactionArgument_U8Vector(TransactionArgument):
    INDEX=4
    value: typing.Sequence[np.uint8]


@dataclass
class _TransactionArgument_Bool(TransactionArgument):
    INDEX=5
    value: np.bool


TransactionArgument.U8 = _TransactionArgument_U8
TransactionArgument.U64 = _TransactionArgument_U64
TransactionArgument.U128 = _TransactionArgument_U128
TransactionArgument.Address = _TransactionArgument_Address
TransactionArgument.U8Vector = _TransactionArgument_U8Vector
TransactionArgument.Bool = _TransactionArgument_Bool
TransactionArgument.VARIANTS = [TransactionArgument.U8, TransactionArgument.U64, TransactionArgument.U128, TransactionArgument.Address, TransactionArgument.U8Vector, TransactionArgument.Bool]

class TransactionAuthenticator:
    pass

@dataclass
class _TransactionAuthenticator_Ed25519(TransactionAuthenticator):
    INDEX=0
    public_key: 'Ed25519PublicKey'
    signature: 'Ed25519Signature'

@dataclass
class _TransactionAuthenticator_MultiEd25519(TransactionAuthenticator):
    INDEX=1
    public_key: 'MultiEd25519PublicKey'
    signature: 'MultiEd25519Signature'

TransactionAuthenticator.Ed25519 = _TransactionAuthenticator_Ed25519
TransactionAuthenticator.MultiEd25519 = _TransactionAuthenticator_MultiEd25519
TransactionAuthenticator.VARIANTS = [TransactionAuthenticator.Ed25519, TransactionAuthenticator.MultiEd25519]

class TransactionPayload:
    pass

@dataclass
class _TransactionPayload_Program(TransactionPayload):
    INDEX=0


@dataclass
class _TransactionPayload_WriteSet(TransactionPayload):
    INDEX=1
    value: 'ChangeSet'


@dataclass
class _TransactionPayload_Script(TransactionPayload):
    INDEX=2
    value: 'Script'


@dataclass
class _TransactionPayload_Module(TransactionPayload):
    INDEX=3
    value: 'Module'


TransactionPayload.Program = _TransactionPayload_Program
TransactionPayload.WriteSet = _TransactionPayload_WriteSet
TransactionPayload.Script = _TransactionPayload_Script
TransactionPayload.Module = _TransactionPayload_Module
TransactionPayload.VARIANTS = [TransactionPayload.Program, TransactionPayload.WriteSet, TransactionPayload.Script, TransactionPayload.Module]

class TypeTag:
    pass

@dataclass
class _TypeTag_Bool(TypeTag):
    INDEX=0


@dataclass
class _TypeTag_U8(TypeTag):
    INDEX=1


@dataclass
class _TypeTag_U64(TypeTag):
    INDEX=2


@dataclass
class _TypeTag_U128(TypeTag):
    INDEX=3


@dataclass
class _TypeTag_Address(TypeTag):
    INDEX=4


@dataclass
class _TypeTag_Signer(TypeTag):
    INDEX=5


@dataclass
class _TypeTag_Vector(TypeTag):
    INDEX=6
    value: 'TypeTag'


@dataclass
class _TypeTag_Struct(TypeTag):
    INDEX=7
    value: 'StructTag'


TypeTag.Bool = _TypeTag_Bool
TypeTag.U8 = _TypeTag_U8
TypeTag.U64 = _TypeTag_U64
TypeTag.U128 = _TypeTag_U128
TypeTag.Address = _TypeTag_Address
TypeTag.Signer = _TypeTag_Signer
TypeTag.Vector = _TypeTag_Vector
TypeTag.Struct = _TypeTag_Struct
TypeTag.VARIANTS = [TypeTag.Bool, TypeTag.U8, TypeTag.U64, TypeTag.U128, TypeTag.Address, TypeTag.Signer, TypeTag.Vector, TypeTag.Struct]

class WriteOp:
    pass

@dataclass
class _WriteOp_Deletion(WriteOp):
    INDEX=0


@dataclass
class _WriteOp_Value(WriteOp):
    INDEX=1
    value: typing.Sequence[np.uint8]


WriteOp.Deletion = _WriteOp_Deletion
WriteOp.Value = _WriteOp_Value
WriteOp.VARIANTS = [WriteOp.Deletion, WriteOp.Value]

@dataclass
class WriteSet:
    value: 'WriteSetMut'

@dataclass
class WriteSetMut:
    write_set: typing.Sequence[typing.Tuple['AccessPath', 'WriteOp']]

