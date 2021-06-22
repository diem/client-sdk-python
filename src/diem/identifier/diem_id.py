# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


def create_diem_id(user_identifier: str, vasp_domain_identifier: str) -> str:
    return user_identifier + "@" + vasp_domain_identifier


def is_diem_id(account_identifier: str) -> bool:
    return "@" in account_identifier


def get_user_identifier_from_diem_id(diem_id: str) -> str:
    return diem_id.split("@", 1)[0]


def get_vasp_identifier_from_diem_id(diem_id: str) -> str:
    return diem_id.split("@", 1)[1]
