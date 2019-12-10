#cython: language_level=3

from libc.stdint cimport *
from libc.stddef cimport *

from pylibra cimport capi

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
        return <bytes> self._c_eh.key[:32]


cdef class AccountResource:
    cdef capi.LibraAccountResource _c_ar
    cdef EventHandle _sent_events
    cdef EventHandle _received_events

    @staticmethod
    def create(lcs_bytes):
        cdef capi.LibraAccountResource _c_ar

        success = capi.libra_LibraAccountResource_from(lcs_bytes, len(lcs_bytes), &_c_ar)
        if success != capi.LibraStatus.OK:
            raise ValueError("Decode failure: error {}", success)

        res = AccountResource()
        res._c_ar = _c_ar
        res._sent_events = EventHandle.create(_c_ar.sent_events)
        res._received_events = EventHandle.create(_c_ar.received_events)
        return res

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
        """Account authentication key"""
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
    def createSignedP2PTransaction(sender_private_key: bytes, receiver, sender_sequence: long, num_coins_libra: long, max_gas_amount=140000, gas_unit_price = 0, expiration_time_secs=5 * 60) -> BytesWrapper:
        cdef uint8_t* buf_ptr
        cdef size_t buf_len

        buf_ptr = NULL
        buf_len = 0

        assert len(sender_private_key) == 32
        assert len(receiver) == 32
        assert sender_sequence >= 0
        assert num_coins_libra > 0

        status = capi.libra_SignedTransactionBytes_from(
             <bytes> sender_private_key[:32],
             <bytes> receiver[:32],
             sender_sequence,
             num_coins_libra,
             max_gas_amount,
             gas_unit_price,
             expiration_time_secs,
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
    def bytes(self):
        return <bytes> self._c_buf_ptr[:self._c_buf_len]


    @property
    def hex(self):
        return bytes.hex(self.bytes)
