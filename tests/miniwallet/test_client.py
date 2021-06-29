# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem.testing.miniwallet import RestClient
from diem import jsonrpc
from typing import Dict
import os, aiohttp, pytest


pytestmark = pytest.mark.asyncio  # pyre-ignore


class MockResponse:
    def __init__(self, text, status):
        self._text = text
        self.status = status

    def raise_for_status(self):
        if self.status != 200:
            raise ValueError(self.status)

    async def text(self):
        return self._text

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


async def test_send_with_json_content_type_user_agent_and_x_test_case(monkeypatch):
    def send_request(method: str, url: str, data: str, headers: Dict[str, str]) -> MockResponse:
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == jsonrpc.client.USER_AGENT_HTTP_HEADER
        assert headers["X-Test-Case"] == os.getenv("PYTEST_CURRENT_TEST").split("::")[-1]
        return create_account_response()

    async with aiohttp.ClientSession() as session:
        monkeypatch.setattr(session, "request", send_request)
        await create_account(session)


async def test_no_x_test_case_for_non_pytest_env(monkeypatch):
    def send_request(method: str, url: str, data: str, headers: Dict[str, str]) -> MockResponse:
        assert "X-Test-Case" not in headers
        return create_account_response()

    async with aiohttp.ClientSession() as session:
        monkeypatch.setattr(session, "request", send_request)
        monkeypatch.delenv("PYTEST_CURRENT_TEST")
        await create_account(session)


async def create_account(session: aiohttp.ClientSession) -> None:
    client = RestClient(name="name", server_url="server", session_factory=lambda: session)
    account = await client.create_account()
    assert account.id == "1234"


def create_account_response() -> MockResponse:
    return MockResponse(b'{"id": "1234"}', 200)
