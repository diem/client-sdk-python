# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

def get_diem_id(user_identifier: str, vasp_domain_identifier: str):
    return user_identifier + "@" + vasp_domain_identifier


def is_diem_id(account_identifier: str) -> bool:
    return "@" in account_identifier


def get_account_identifier_with_diem_id(diem_id: str):
    pass
