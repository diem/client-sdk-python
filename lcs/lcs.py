import yaml


def lcs_de_u8(content: bytes) -> (int, bytes):
    res = int.from_bytes(content[0:1], byteorder='little')
    leftover = content[1:]

    return res, leftover


def lcs_de_u32(content: bytes) -> (int, bytes):
    res = int.from_bytes(content[0:4], byteorder='little')
    leftover = content[4:]

    return res, leftover


def lcs_de_u64(content: bytes) -> (int, bytes):
    res = int.from_bytes(content[0:8], byteorder='little')
    leftover = content[8:]

    return res, leftover


def lcs_de_bytes(content):
    count, content = lcs_de_u32(content)

    res = []
    for i in range(count):
        result, content = lcs_de_u8(content)
        res.append(result)
    print("Bytes: ", list(map(hex, res)))
    return res, content


def lcs_de_primitives(content: bytes, type):
    if type == "U8":
        return lcs_de_u8(content)

    if type == "U32":
        return lcs_de_u32(content)

    if type == "U64":
        return lcs_de_u64(content)

    if type == "Bytes":
        return lcs_de_bytes(content)

    if 'Tuple' in type:
        return lcs_de_tuple("", content, type['Tuple'])

    raise ValueError("Not supported: ", type)


def lcs_de_tag(content: bytes) -> (int, bytes):
    res, leftover = lcs_de_primitives(content, "U32")
    return res, leftover


def lcs_de_tuple(prefix, content, items):
    res = []
    for item in items:
        result, content = lcs_de_primitives(content, item)
        res.append(result)
    print(prefix, "Tuple: ", list(map(hex, res)))

    return res, content


def lcs_de_seq(prefix, lcs_data, content, item):
    count, content = lcs_de_u32(content)

    res = []
    for i in range(count):
        if 'Ident' in item:
            result, content = lcs_from_bytes(prefix + "--", lcs_data, content, item['Ident'])
        else:
            result, content = lcs_de_primitives(content, item)
        res.append(result)

    # print(prefix, "Seq: ", res)

    return res, content


def lcs_de_struct(prefix, lcs_data, content, rootname):
    print(prefix, "Struct: ", rootname)
    root = lcs_data[rootname]['Struct']

    for i in range(len(root)):
        field_name = list(root[i].keys())[0]
        field_type = root[i][field_name]

        if 'Ident' in field_type:
            print(prefix + "--", "Field:", field_name, ", Type:", field_type)
            res, content = lcs_from_bytes(prefix + "--", lcs_data, content, field_type['Ident'])
        elif 'Tuple' in field_type:
            res, content = lcs_de_tuple(prefix + "--", content, field_type['Tuple'])
            print(prefix + "--", "Field:", field_name, ", Type:", field_type, ", Value: ", res)
        elif 'Seq' in field_type:
            res, content = lcs_de_seq(prefix + "--", lcs_data, content, field_type['Seq'])
            print(prefix + "--", "Field:", field_name, ", Type:", field_type, ", Value: ", res)
        else:
            res, content = lcs_de_primitives(content, field_type)
            print(prefix + "--", "Field:", field_name, ", Type:", field_type, ", Value: ", res)
    return res, content


def lcs_de_variant(prefix, lcs_data, content, rootname):
    print(prefix, rootname)

    root = lcs_data[rootname]
    tags = root["Variant"].keys()

    tag, content = lcs_de_tag(content)

    if tag not in tags:
        raise ValueError("Unknown tags: ", tag, "possible: ", tags)

    root = root["Variant"][tag]

    variant_name = list(root.keys())[0]

    if "Ident" in root[variant_name]["NewType"]:
        inner_type = root[variant_name]["NewType"]["Ident"]
        print(prefix, "Variant: ", variant_name, ", Inner Type: ", inner_type)
        res, content = lcs_from_bytes(prefix + "--", lcs_data, content, inner_type)
    else:
        inner_type = root[variant_name]["NewType"]
        res, content = lcs_de_primitives(content, inner_type)
        print(prefix, "Variant: ", variant_name, ", Inner Type: ", inner_type, ", Value:", res)

    return res, content


def lcs_from_bytes(prefix, lcs_data, content: bytes, rootname: str):
    root = lcs_data[rootname]

    if "Variant" in root:
        return lcs_de_variant(prefix + "--", lcs_data, content, rootname)

    if "Struct" in root:
        return lcs_de_struct(prefix + "--", lcs_data, content, rootname)

    if "Tuple" in root:
        return lcs_de_tuple(prefix + "--", content, root["Tuple"])

    raise ValueError("Unhandled types: ", root)


SIGNED_TXN_BYTES: bytes = bytes.fromhex(
    "000000000077c0b997f422ee27c92fef464f81570d55c1cdc8e0f289969d48f142609ff9000000000000000002000000b4000000a11ceb0b010007014600000004000000034a000000060000000c50000000060000000d5600000006000000055c0000002900000004850000002000000007a50000000f00000000000002000100010300020002050300030205030300063c53454c463e046d61696e0c4c696272614163636f756e740f7061795f66726f6d5f73656e6465720000000000000000000000000000000000000000000000000000000000000000000000020004000b000b01120101020200000001000000000000000000000000000000000000000000000000000000000000000a550c180000000040420f0000000000e02202000000000000000000000000001bc6385d00000000200000006b161b5ec657ed538da35a0aac41efd45e0556624061d9f937e967c7708c80f440000000563c13a32c9b0163388fd0f31a2c4ff0d2de301cb3c32d7fb6b4058aab1a25cf60f6527532afa34d3b3145c15bfeff2329bb05b1eaea4487920ca622fba1c20e"
)


with open('transaction.yaml', 'r') as f:
    lcs_data = yaml.safe_load(f)

res, content = lcs_from_bytes('', lcs_data, SIGNED_TXN_BYTES, "Transaction")

print("Left Over: ", content)
