#cython: language_level=3

from pylibra cimport capi


def account_resource_from_lcs(blob: bytes):
    return capi.account_resource_from_lcs(blob, len(blob))
