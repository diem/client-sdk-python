# distutils: include_dirs = ../libra-dev/include/

cdef extern from "data.h":
    ctypedef struct CDevAccountResource:
        long balance

    CDevAccountResource account_resource_from_lcs(char* buffer, int length)


cdef class DevAccountResource:
    cdef public long balance

    def __cinit__(self, lcs_bytes):
        self.balance = account_resource_from_lcs(lcs_bytes, len(lcs_bytes)).balance
