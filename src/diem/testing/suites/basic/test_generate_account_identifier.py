# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem.testing.miniwallet import RestClient
from diem import identifier


def test_generate_account_identifier(target_client: RestClient, hrp: str) -> None:
    account = target_client.create_account()
    account_identifier = account.generate_account_identifier()
    account_address, _ = identifier.decode_account(account_identifier, hrp)
    assert account_address
