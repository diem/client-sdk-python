#cython: language_level=3

from libc.stdint cimport *
from libc.stddef cimport *


cdef extern from "data.h":
    enum LibraStatus:
        OK = 1
        InvalidArgument = -1
        InternalError = -255

    struct LibraEventHandle:
        uint64_t count
        uint8_t[32] key

    struct LibraAccountResource:
        uint64_t balance
        uint64_t sequence
        uint8_t* authentication_key
        bint delegated_key_rotation_capability
        bint delegated_withdrawal_capability
        LibraEventHandle sent_events
        LibraEventHandle received_events


    LibraStatus libra_LibraAccountResource_from(const uint8_t *, size_t length, LibraAccountResource* out)
