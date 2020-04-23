# pyre-ignore-all-errors

import dataclasses
import collections

import numpy as np
import typing
from typing import get_type_hints
from ._libra_types import *

prefix = []


def lcs_encode_u32_as_uleb128(value: int) -> bytes:
    global prefix

    res = b""
    while value >= 0x80:
        res += ((value & 0x7F) | 0x80).to_bytes(1, "little", signed=False)
        value >>= 7
    res += value.to_bytes(1, "little", signed=False)

    print(prefix, "u32_as_uleb128: ", value, res)
    return res


def lcs_decode_uleb128_as_u32(content: bytes) -> typing.Tuple[int, bytes]:
    global prefix

    value = 0
    for shift in range(0, 32, 7):
        byte = int.from_bytes(content[0:1], "little", signed=False)
        content = content[1:]
        digit = byte & 0x7F
        print(byte, digit)
        value |= digit << shift
        if digit == byte:
            if shift > 0 and digit == 0:
                raise ValueError("invalid uleb128 number")
            break

    print(prefix, "uleb128_as_u32", value)
    return value, content


def lcs_decode_str(content: bytes) -> typing.Tuple[str, bytes]:
    global prefix

    strlen, content = lcs_decode_uleb128_as_u32(content)
    val, content = content[0:strlen].decode(), content[strlen:]

    print(prefix, "String: ", val)
    return val, content


def lcs_decode_bytes(content: bytes) -> typing.Tuple[bytes, bytes]:
    global prefix

    len, content = lcs_decode_uleb128_as_u32(content)
    val, content = content[:len], content[len:]

    print(prefix, "Bytes: ", val)
    return val, content


def lcs_encode_str(value: str) -> bytes:
    global prefix
    print(prefix, "String: ", value)
    return lcs_encode_u32_as_uleb128(len(value)) + value.encode()


def lcs_encode_bytes(value: bytes) -> bytes:
    global prefix
    print(prefix, "Bytes: ", value)
    return lcs_encode_u32_as_uleb128(len(value)) + value


lcs_primitive_map = {
    np.uint8: lambda x: int(x).to_bytes(1, "little", signed=False),
    np.uint16: lambda x: int(x).to_bytes(2, "little", signed=False),
    np.uint32: lambda x: int(x).to_bytes(4, "little", signed=False),
    np.uint64: lambda x: int(x).to_bytes(8, "little", signed=False),
    str: lambda x: lcs_encode_str(x),
    bytes: lambda x: lcs_encode_bytes(x),
}

lcs_primitive_deser_map = {
    np.uint8: lambda content: (int.from_bytes(content[0:1], byteorder="little"), content[1:]),
    np.uint16: lambda content: (int.from_bytes(content[0:2], byteorder="little"), content[2:]),
    np.uint32: lambda content: (int.from_bytes(content[0:4], byteorder="little"), content[4:]),
    np.uint64: lambda content: (int.from_bytes(content[0:8], byteorder="little"), content[8:]),
    str: lambda content: lcs_decode_str(content),
    bytes: lambda content: lcs_decode_bytes(content),
}


# noqa: C901
def lcs_bytes(obj: typing.Any, lcs_type) -> bytes:
    global prefix
    result = b""

    if lcs_type in lcs_primitive_map:
        print(prefix, "primitive: ", obj, lcs_type)
        prefix.append("--")
        result += lcs_primitive_map[lcs_type](obj)
        prefix.pop()
    elif hasattr(lcs_type, "__origin__"):  # Generics
        if getattr(lcs_type, "__origin__") == collections.abc.Sequence:  # Generic sequence
            sub_type = getattr(lcs_type, "__args__")[0]
            result += lcs_encode_u32_as_uleb128(len(obj))
            result += b"".join([lcs_bytes(item, sub_type) for item in obj])
        elif getattr(lcs_type, "__origin__") == tuple:  # Generic Tuple
            for i in range(len(obj)):
                sub_type = getattr(lcs_type, "__args__")[i]
                result += lcs_bytes(obj[i], sub_type)
        else:
            raise NotImplementedError
    else:
        if not isinstance(obj, lcs_type):
            raise ValueError("Wrong Value for the type", obj, lcs_type)

        if obj.__class__ != lcs_type and issubclass(obj.__class__, lcs_type):
            print(prefix, "Variant: ", obj.__class__)

            prefix.append("--")
            result += lcs_encode_u32_as_uleb128(obj.__class__.INDEX)

            typing_hints = get_type_hints(obj.__class__)
            for (key, val) in obj.__dict__.items():
                if key.startswith("__"):
                    continue
                print(prefix, "field: ", key, typing_hints[key], type(val))
                result += lcs_bytes(val, typing_hints[key])
            prefix.pop()
        else:
            print(prefix, "Struct: ", lcs_type)
            prefix.append("--")
            typing_hints = get_type_hints(obj.__class__)
            for (key, val) in obj.__dict__.items():
                if key.startswith("__"):
                    continue
                print(prefix, "field: ", key, typing_hints[key], type(val))
                result += lcs_bytes(val, typing_hints[key])
            prefix.pop()

    return result


# noqa
def lcs_from_bytes(content: bytes, lcs_type):
    global prefix

    if lcs_type in lcs_primitive_deser_map:
        print(prefix, "primitive: ", lcs_type)

        prefix.append("--")
        res, content = lcs_primitive_deser_map[lcs_type](content)
        prefix.pop()

        return res, content
    elif hasattr(lcs_type, "__origin__"):  # Generics
        if getattr(lcs_type, "__origin__") == collections.abc.Sequence:  # Generic sequence
            prefix.append("--")

            sub_type = getattr(lcs_type, "__args__")[0]
            seqlen, content = lcs_decode_uleb128_as_u32(content)
            res = []
            for i in range(0, seqlen):
                item, content = lcs_from_bytes(content, sub_type)
                res.append(item)

            prefix.pop()

            return res, content
        elif getattr(lcs_type, "__origin__") == tuple:  # Generic Tuple
            prefix.append("--")

            res = []
            args = getattr(lcs_type, "__args__")
            for i in range(len(args)):
                sub_type = args[i]
                item, content = lcs_from_bytes(content, sub_type)
                res.append(item)

            prefix.pop()

            return tuple(res), content
        else:
            raise NotImplementedError
    else:
        # handle structs
        if dataclasses.is_dataclass(lcs_type):
            print(prefix, "Struct: ", lcs_type)
            prefix.append("--")

            values = []
            fields = dataclasses.fields(lcs_type)
            typing_hints = get_type_hints(lcs_type)
            for field in fields:
                field_type = typing_hints[field.name]
                print(prefix, "Field: ", field_type)
                field_value, content = lcs_from_bytes(content, field_type)
                values.append(field_value)

            res = lcs_type(*values)

            prefix.pop()
            return res, content
        # handle variant
        elif hasattr(lcs_type, "VARIANTS"):
            print(prefix, "Variant: ", lcs_type)
            variant_index, content = lcs_decode_uleb128_as_u32(content)
            new_type = lcs_type.VARIANTS[variant_index]

            prefix.append("--")
            res, content = lcs_from_bytes(content, new_type)
            prefix.pop()

            return res, content
        else:
            raise NotImplementedError
