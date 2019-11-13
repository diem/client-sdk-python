#cython: language_level=3

from pylibra cimport capi

cdef class EventHandle(object):
    cdef capi.CEventHandle _c_eh

    @staticmethod
    cdef create(capi.CEventHandle c_event_handle):
        r = EventHandle()
        r._c_eh = c_event_handle
        return r

    @property
    def count(self):
        return self._c_eh.count

    @property
    def key(self):
        return <bytes> self._c_eh.key[:32]


cdef class AccountResource(object):
    cdef capi.CDevAccountResource _c_ar
    cdef EventHandle _sent_events
    cdef EventHandle _received_events

    def __cinit__(self, lcs_bytes):
        """Create AccountResource from AccountStateBlob."""
        _c_ar = capi.account_resource_from_lcs(lcs_bytes, len(lcs_bytes))
        self._c_ar = _c_ar
        self._sent_events = EventHandle.create(_c_ar.sent_events)
        self._received_events = EventHandle.create(_c_ar.received_events)

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
