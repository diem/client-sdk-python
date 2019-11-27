#cython: language_level=3

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
        if capi.libra_LibraAccountResource_from(lcs_bytes, len(lcs_bytes), &_c_ar) != capi.LibraStatus.OK:
            raise ValueError("Decode failure")

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
