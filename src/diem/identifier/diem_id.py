# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


def create_diem_id(user_identifier: str, vasp_domain_identifier: str) -> str:
    diem_id = user_identifier + "@" + vasp_domain_identifier
    if not is_diem_id(diem_id):
        raise ValueError(f"{diem_id} is not a valid DiemID.")
    return diem_id


def is_diem_id(account_identifier: str) -> bool:
    if "@" not in account_identifier:
        return False

    user_identifier = account_identifier.split("@", 1)[0]
    vasp_identifier = account_identifier.split("@", 1)[1]
    if len(user_identifier) > 64 or len(vasp_identifier) > 63:
        return False
    for ch in user_identifier:
        if not ch.isalnum() and ch != ".":
            return False
    for ch in vasp_identifier:
        if not ch.isalnum() and ch != ".":
            return False
    return True


def get_user_identifier_from_diem_id(diem_id: str) -> str:
    if not is_diem_id(diem_id):
        raise ValueError(f"{diem_id} is not a valid DiemID.")
    return diem_id.split("@", 1)[0]


def get_vasp_identifier_from_diem_id(diem_id: str) -> str:
    if not is_diem_id(diem_id):
        raise ValueError(f"{diem_id} is not a valid DiemID.")
    return diem_id.split("@", 1)[1]
