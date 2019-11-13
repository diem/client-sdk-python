#cython: language_level=3

from pylibra cimport capi

def account_resource_from_lcs(a, b):
    return capi.account_resource_from_lcs(a, b)