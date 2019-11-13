#cython: language_level=3

from libc.stdint cimport *
from libc.stddef cimport *

cdef extern from "data.h":
    cdef struct CEventHandle:
        uint64_t count
        uint8_t[32] key

    cdef struct CDevAccountResource:
        uint64_t balance
        uint64_t sequence
        uint8_t* authentication_key
        bint delegated_key_rotation_capability
        bint delegated_withdrawal_capability
        CEventHandle sent_events
        CEventHandle received_events


    CDevAccountResource account_resource_from_lcs(const uint8_t *, size_t length)