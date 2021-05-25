# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain, jsonrpc
from diem.testing.miniwallet import RestClient, AppConfig
import uuid


def test_send_ping_command(
    stub_config: AppConfig,
    target_client: RestClient,
    stub_client: RestClient,
    diem_client: jsonrpc.Client,
    hrp: str,
) -> None:
    """
    Test Plan:
    1. Create a new test account in the target wallet application.
    2. Generate a new account identifier from the new test account.
    3. Send a ping command request to the generated account identifier.
    4. Expect response status is success, and response cid is same with request cid.
    5. Send another ping command request to the generated account identifier.
    6. Expect response status is success.
    7. Expect cid is different for the 2 response status.
    """

    receiver_address = target_client.create_account().generate_account_identifier()
    offchain_client = offchain.Client(stub_config.account.account_address, diem_client, hrp)
    cid = str(uuid.uuid4())
    resp = offchain_client.ping(receiver_address, stub_config.account.compliance_key.sign, cid=cid)
    assert resp.cid == cid
    assert resp.status == "success"
    assert resp.error is None

    resp2 = offchain_client.ping(receiver_address, stub_config.account.compliance_key.sign)
    assert resp2.cid
    assert resp2.status == "success"
    assert resp2.error is None

    assert resp.cid != resp2.cid
