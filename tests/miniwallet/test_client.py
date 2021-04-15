# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem.testing.miniwallet import RestClient
from diem import jsonrpc
from typing import Dict
import requests, os


def test_send_with_json_content_type_user_agent_and_x_test_case(monkeypatch):
    def send_request(method: str, url: str, data: str, headers: Dict[str, str]) -> requests.Response:
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == jsonrpc.client.USER_AGENT_HTTP_HEADER
        assert headers["X-Test-Case"] == os.getenv("PYTEST_CURRENT_TEST")
        return create_account_response()

    session = requests.Session()
    monkeypatch.setattr(session, "request", send_request)
    create_account(session)


def test_no_x_test_case_for_non_pytest_env(monkeypatch):
    def send_request(method: str, url: str, data: str, headers: Dict[str, str]) -> requests.Response:
        assert "X-Test-Case" not in headers
        return create_account_response()

    session = requests.Session()
    monkeypatch.setattr(session, "request", send_request)
    monkeypatch.delenv("PYTEST_CURRENT_TEST")
    create_account(session)


def create_account(session: requests.Session) -> None:
    client = RestClient(name="name", server_url="server", session=session)
    client.create_account()


def create_account_response() -> requests.Response:
    resp = requests.Response()
    resp.status_code = 200
    resp._content = b'{"id": "1"}'
    return resp
