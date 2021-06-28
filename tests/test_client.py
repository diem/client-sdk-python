# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import jsonrpc
import pytest, aiohttp, asyncio


pytestmark = pytest.mark.asyncio  # pyre-ignore


async def test_update_last_known_state():
    client = jsonrpc.Client("url")
    assert client.get_last_known_state() is not None

    client.update_last_known_state(2, 2, 2)
    assert client.get_last_known_state() is not None
    assert client.get_last_known_state().chain_id == 2
    assert client.get_last_known_state().version == 2
    assert client.get_last_known_state().timestamp_usecs == 2

    # chain id mismatch will raise invalid server response instead of
    # stale response error
    with pytest.raises(jsonrpc.InvalidServerResponse):
        client.update_last_known_state(1, 1, 1)

    with pytest.raises(jsonrpc.StaleResponseError):
        client.update_last_known_state(2, 1, 2)
    with pytest.raises(jsonrpc.StaleResponseError):
        client.update_last_known_state(2, 2, 1)
    with pytest.raises(jsonrpc.StaleResponseError):
        client.update_last_known_state(2, 1, 1)

    client.update_last_known_state(2, 2, 2)
    assert client.get_last_known_state().chain_id == 2
    assert client.get_last_known_state().version == 2
    assert client.get_last_known_state().timestamp_usecs == 2

    client.update_last_known_state(2, 3, 3)
    assert client.get_last_known_state().chain_id == 2
    assert client.get_last_known_state().version == 3
    assert client.get_last_known_state().timestamp_usecs == 3


async def test_invalid_server_url():
    client = jsonrpc.Client("url")
    with pytest.raises(aiohttp.InvalidURL):
        await client.get_currencies()


async def test_first_success_strategy_returns_first_completed_success_response():
    rs = jsonrpc.RequestWithBackups(backups=["backup"])
    client = jsonrpc.Client("primary", rs=rs)

    client._send_http_request = gen_metadata_response(client, snap="primary")
    metadata = await client.get_metadata()
    assert metadata.script_hash_allow_list == ["backup"]

    client._send_http_request = gen_metadata_response(client, snap="backup")
    metadata = await client.get_metadata()
    assert metadata.script_hash_allow_list == ["primary"]


async def test_fallback_to_second_if_first_failed():
    rs = jsonrpc.RequestWithBackups(backups=["backup"])
    client = jsonrpc.Client("primary", rs=rs)

    # primary will fail immediately, backup is slow but success
    client._send_http_request = gen_metadata_response(client, fail="primary", snap="backup")
    metadata = await client.get_metadata()
    assert metadata.script_hash_allow_list == ["backup"]


async def test_fallback_strategy_always_returns_primary_response_if_it_successes():
    client = jsonrpc.Client(
        "primary",
        rs=jsonrpc.RequestWithBackups(backups=["backup"], fallback=True),
    )
    client._send_http_request = gen_metadata_response(client)
    for _ in range(10):
        metadata = await client.get_metadata()
        assert metadata.script_hash_allow_list == ["primary"]


async def test_fallback_to_backups_when_primary_failed():
    client = jsonrpc.Client(
        "primary",
        rs=jsonrpc.RequestWithBackups(backups=["backup"], fallback=True),
    )
    client._send_http_request = gen_metadata_response(client, fail="primary")
    for _ in range(10):
        metadata = await client.get_metadata()
        assert metadata.script_hash_allow_list == ["backup"]


async def test_raises_error_if_primary_and_backup_both_failed():
    client = jsonrpc.Client("url", rs=jsonrpc.RequestWithBackups(backups=["url"]))
    with pytest.raises(aiohttp.InvalidURL):
        assert await client.get_currencies()

    client = jsonrpc.Client("url", rs=jsonrpc.RequestWithBackups(backups=["url"], fallback=True))
    with pytest.raises(aiohttp.InvalidURL):
        assert await client.get_currencies()


def gen_metadata_response(client, fail=None, snap=None):
    async def send_request(url, request, ignore_stale_response):
        if fail == url:
            raise jsonrpc.StaleResponseError("error")

        if snap == url:
            await asyncio.sleep(0.1)

        state = client.get_last_known_state()
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"script_hash_allow_list": [url]},
            "diem_chain_id": state.chain_id,
            "diem_ledger_timestampusec": state.timestamp_usecs,
            "diem_ledger_version": state.version,
        }

    return send_request
