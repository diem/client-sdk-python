# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem.testing.miniwallet import RestClient
from diem import jsonrpc
from typing import Dict
import requests


def test_send_with_json_content_type(monkeypatch):
    session = requests.Session()
    resp = requests.Response()
    resp.status_code = 200
    resp._content = b'{"id": "1"}'

    def assert_request(method: str, url: str, data: str, headers: Dict[str, str]) -> requests.Response:
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == jsonrpc.client.USER_AGENT_HTTP_HEADER
        return resp

    monkeypatch.setattr(session, "request", assert_request)
    client = RestClient(name="name", server_url="server", session=session)
    client.create_account()
