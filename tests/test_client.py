# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0


from libra import jsonrpc
import pytest


def test_update_last_known_state():
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


def test_invalid_server_url():
    client = jsonrpc.Client("url")
    with pytest.raises(jsonrpc.NetworkError):
        client.get_currencies()
