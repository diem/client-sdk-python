#cython: language_level=3

from libc.stdint cimport *
from libc.stddef cimport *
from libc.string cimport memset

from . cimport capi

import time
from ._types import SignedTransaction, AccountKey


cdef class TransactionUtils:
    @staticmethod
    def createSignedP2PTransaction(sender_private_key: bytes, receiver: bytes, receiver_authkey_prefix: bytes, sender_sequence: int, num_coins_microlibra: int, *ignore, expiration_time: int, max_gas_amount :int = 1_000_000, gas_unit_price:int = 0, metadata: bytes = b'') -> bytes:
        """createSignedP2PTransaction"""
        cdef uint8_t* buf_ptr
        cdef size_t buf_len

        buf_ptr = NULL
        buf_len = 0

        if not len(sender_private_key) == capi.LIBRA_CONST._LIBRA_PRIVKEY_SIZE:
            raise ValueError("Invalid private key!")

        if not len(receiver) == capi.LIBRA_CONST._LIBRA_ADDRESS_SIZE:
            raise ValueError("Invalid receiver address!")

        if not len(receiver_authkey_prefix) == capi.LIBRA_CONST._LIBRA_PUBKEY_SIZE - capi.LIBRA_CONST._LIBRA_ADDRESS_SIZE:
            raise ValueError("Invalid receiver authkey prefix!")

        if not sender_sequence >= 0:
            raise ValueError("Invalid sender_sequence!")

        if not num_coins_microlibra > 0:
            raise ValueError("Invalid num_coins_microlibra!")

        receiver_authkey = receiver_authkey_prefix + receiver

        status = capi.libra_SignedTransactionBytes_from(
             <bytes> sender_private_key[:len(sender_private_key)],
             <bytes> receiver_authkey[:len(receiver_authkey)],
             sender_sequence,
             num_coins_microlibra,
             max_gas_amount,
             gas_unit_price,
             expiration_time,
             metadata,
             len(metadata),
             &buf_ptr, &buf_len)

        if status != capi.LibraStatus.Ok:
            raise ValueError("libra_SignedTransactionBytes_from failed: %d", status)

        result = <bytes> buf_ptr[:buf_len]
        capi.libra_free_bytes_buffer(buf_ptr)

        return result


    @staticmethod
    def parse(version: int, lcs_bytes: bytes, gas: int) -> SignedTransaction:
        """Create SignedTranscation from bytes."""
        cdef NativeSignedTransaction res = NativeSignedTransaction.__new__(NativeSignedTransaction)

        success = capi.libra_LibraSignedTransaction_from(lcs_bytes, len(lcs_bytes), &res._c_signed_txn)
        if success != capi.LibraStatus.Ok:
            raise ValueError("SignedTranscation fail to decode, error: %s." % success)
        res._c_txn = res._c_signed_txn.raw_txn
        res._version = version
        res._gas_used = gas
        return res


class NativeAccountKey(AccountKey):
    """AccountKey"""
    def __init__(self, private_key_bytes: bytes):
        """create AccountKey from private_key_bytes"""
        if not isinstance(private_key_bytes, bytes) or len(private_key_bytes) != capi.LIBRA_CONST._LIBRA_PRIVKEY_SIZE:
            raise ValueError("Invalid private key.")
        cdef capi.LibraAccountKey _c_ak
        success = capi.libra_LibraAccountKey_from(private_key_bytes, &_c_ak)
        if success != capi.LibraStatus.Ok:
            raise ValueError("Decode error: invalid private key.")
        self._addr = <bytes> _c_ak.address[:sizeof(_c_ak.address)]
        self._privkey = <bytes> _c_ak.private_key[:sizeof(_c_ak.private_key)]
        self._pubkey = <bytes> _c_ak.public_key[:sizeof(_c_ak.public_key)]

        import hashlib
        h = hashlib.sha3_256()
        h.update(self._pubkey)
        h.update(b'\x00') # Scheme: single key
        self._authkey = h.digest()

    @property
    def address(self) -> bytes:
        return self._addr

    @property
    def public_key(self) -> bytes:
        return self._pubkey

    @property
    def private_key(self) -> bytes:
        return self._privkey

    @property
    def authentication_key(self) -> bytes:
        return self._authkey

class AccountKeyUtils:
    @staticmethod
    def from_private_key(private_bytes) -> AccountKey:
        return NativeAccountKey(private_bytes)


cdef class NativeTransaction:
    cdef capi.LibraRawTransaction _c_txn

    @property
    def sender(self) -> bytes:
        return <bytes> self._c_txn.sender[:sizeof(self._c_txn.sender)]

    @property
    def sequence(self) -> int:
        return self._c_txn.sequence_number

    @property
    def max_gas_amount(self) -> int:
        return self._c_txn.max_gas_amount

    @property
    def gas_unit_price(self) -> int:
        return self._c_txn.gas_unit_price

    @property
    def expiration_time(self) -> int:
        return self._c_txn.expiration_time_secs

    @property
    def is_p2p(self) -> bool:
        return self._c_txn.payload.txn_type == capi.TransactionType.PeerToPeer

    @property
    def is_mint(self) -> bool:
        return self._c_txn.payload.txn_type == capi.TransactionType.Mint

    @property
    def receiver(self) -> bytes:
        assert self.is_p2p or self.is_mint
        return <bytes> self._c_txn.payload.args.address[:sizeof(self._c_txn.payload.args.address)]

    @property
    def amount(self) -> int:
        assert self.is_p2p or self.is_mint
        return self._c_txn.payload.args.value

    @property
    def metadata(self) -> bytes:
        return <bytes> self._c_txn.payload.args.metadata_bytes[:self._c_txn.payload.args.metadata_len]


cdef class NativeSignedTransaction(NativeTransaction):
    cdef capi.LibraSignedTransaction _c_signed_txn
    cdef int _version
    cdef int _gas_used

    @property
    def public_key(self) -> bytes:
        return <bytes> self._c_signed_txn.public_key[:sizeof(self._c_signed_txn.public_key)]

    @property
    def signature(self) -> bytes:
        return <bytes> self._c_signed_txn.signature[:sizeof(self._c_signed_txn.signature)]

    @property
    def version(self) -> int:
        return self._version

    @property
    def gas(self) -> int:
        return self._gas_used
