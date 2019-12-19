#cython: language_level=3

from libc.stdint cimport *
from libc.stddef cimport *
from libc.string cimport memset

from pylibra cimport capi
import time

cdef class EventHandle:
    cdef capi.LibraEventHandle _c_eh

    @staticmethod
    cdef create(capi.LibraEventHandle c_eh):
        res = EventHandle()
        res._c_eh = c_eh
        return res

    @property
    def count(self):
        return self._c_eh.count

    @property
    def key(self):
        return <bytes> self._c_eh.key[:40]


cdef class AccountResource:
    cdef capi.LibraAccountResource _c_ar
    cdef EventHandle _sent_events
    cdef EventHandle _received_events
    cdef bytes _address

    @staticmethod
    def create(addr_bytes, lcs_bytes):
        cdef capi.LibraAccountResource _c_ar

        if not isinstance(addr_bytes, bytes) or len(addr_bytes) != 32:
            raise ValueError("Invalid account address")

        if len(lcs_bytes):
            success = capi.libra_LibraAccountResource_from(lcs_bytes, len(lcs_bytes), &_c_ar)
            if success != capi.LibraStatus.OK:
                raise ValueError("AccountResource Decode failure: error {}", success)
        else:
            memset(&_c_ar, 0, sizeof(_c_ar))
            _c_ar.authentication_key = addr_bytes[:32]

        res = AccountResource()
        res._address = addr_bytes
        res._c_ar = _c_ar
        res._sent_events = EventHandle.create(_c_ar.sent_events)
        res._received_events = EventHandle.create(_c_ar.received_events)
        return res

    @property
    def address(self):
        """Account address in bytes"""
        return self._address

    @property
    def balance(self):
        """Account balance"""
        return self._c_ar.balance

    @property
    def sequence(self):
        """Account sequence number"""
        return self._c_ar.sequence

    @property
    def authentication_key(self):
        """Account authentication key, could be different than account address"""
        return <bytes> self._c_ar.authentication_key[:32]

    @property
    def delegated_key_rotation_capability(self):
        return self._c_ar.delegated_key_rotation_capability

    @property
    def delegated_withdrawal_capability(self):
        return self._c_ar.delegated_withdrawal_capability

    @property
    def sent_events(self):
        return self._sent_events

    @property
    def received_events(self):
        return self._received_events


cdef class TransactionUtils:
    @staticmethod
    def createSignedP2PTransaction(sender_private_key: bytes, receiver: bytes, sender_sequence: int, num_coins_microlibra: int, *ignore, expiration_time: int, max_gas_amount=140000, gas_unit_price = 0) -> BytesWrapper:
        cdef uint8_t* buf_ptr
        cdef size_t buf_len

        buf_ptr = NULL
        buf_len = 0

        assert len(sender_private_key) == 32
        assert len(receiver) == 32
        assert sender_sequence >= 0
        assert num_coins_microlibra > 0

        status = capi.libra_SignedTransactionBytes_from(
             <bytes> sender_private_key[:32],
             <bytes> receiver[:32],
             sender_sequence,
             num_coins_microlibra,
             max_gas_amount,
             gas_unit_price,
             expiration_time,
             &buf_ptr, &buf_len)

        if status != capi.LibraStatus.OK:
            raise ValueError("libra_SignedTransactionBytes_from failed: %d", status)

        return BytesWrapper.create(buf_ptr, buf_len)


cdef class BytesWrapper:
    cdef uint8_t* _c_buf_ptr
    cdef size_t _c_buf_len

    @staticmethod
    cdef create(uint8_t* buf_ptr, size_t buf_len):
        assert buf_ptr != NULL
        assert buf_len > 0

        cdef BytesWrapper res = BytesWrapper.__new__(BytesWrapper)
        res._c_buf_ptr = buf_ptr
        res._c_buf_len = buf_len
        return res

    def __dealloc__(self):
        capi.libra_free_bytes_buffer(self._c_buf_ptr)

    @property
    def byte(self):
        return <bytes> self._c_buf_ptr[:self._c_buf_len]


    @property
    def hex(self):
        return bytes.hex(self.byte)


class AccountKey:
    def __init__(self, private_key_bytes):
        if not isinstance(private_key_bytes, bytes) or len(private_key_bytes) != 32:
            raise ValueError("Invalid private key.")
        cdef capi.LibraAccountKey _c_ak
        success = capi.libra_LibraAccount_from(private_key_bytes, &_c_ak)
        if success != capi.LibraStatus.OK:
            raise ValueError("Decode error: invalid private key.")
        self._addr = <bytes> _c_ak.address[:32]
        self._privkey = <bytes> _c_ak.private_key[:32]
        self._pubkey = <bytes> _c_ak.public_key[:32]

    @property
    def address(self):
        return self._addr

    @property
    def public_key(self):
        return self._pubkey

    @property
    def private_key(self):
        return self._privkey
