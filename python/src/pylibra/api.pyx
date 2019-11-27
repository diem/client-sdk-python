#cython: language_level=3

from pylibra cimport capi


def libra_LibraAccountRsource_from(blob: bytes) -> (capi.LibraStatus, capi.LibraAccountResource):
    cdef capi.LibraAccountResource result
    return (capi.libra_LibraAccountResource_from(blob, len(blob), &result), result)
