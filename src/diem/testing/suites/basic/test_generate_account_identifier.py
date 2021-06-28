# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem.testing.miniwallet import RestClient
from diem import identifier
import pytest


pytestmark = pytest.mark.asyncio  # pyre-ignore


async def test_generate_account_identifier(target_client: RestClient, hrp: str) -> None:
    account = await target_client.create_account()
    account_identifier = await account.generate_account_identifier()
    account_address, _ = identifier.decode_account(account_identifier, hrp)
    assert account_address
