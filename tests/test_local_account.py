# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import utils, LocalAccount


def test_from_private_key_hex():
    account = LocalAccount.generate()
    hex_key = utils.private_key_bytes(account.private_key).hex()
    new_account = LocalAccount.from_private_key_hex(hex_key)
    assert utils.private_key_bytes(new_account.private_key).hex() == hex_key
