# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from os import getenv, environ
from typing import Optional, Dict, Any


TARGET_URL: str = "DMW_TEST_TARGET"
TEST_DEBUG_API: str = "DMW_TEST_DEBUG_API"
SELF_CHECK: str = "DMW_SELF_CHECK"

DMW_STUB_BIND_HOST: str = "DMW_STUB_BIND_HOST"
DMW_STUB_BIND_PORT: str = "DMW_STUB_BIND_PORT"
DMW_STUB_DIEM_ACCOUNT_BASE_URL: str = "DMW_STUB_DIEM_ACCOUNT_BASE_URL"
DMW_STUB_DIEM_ACCOUNT_CONFIG: str = "DMW_STUB_DIEM_ACCOUNT_CONFIG"


def dmw_stub_diem_account_config() -> Optional[str]:
    return getenv(DMW_STUB_DIEM_ACCOUNT_CONFIG)


def dmw_stub_diem_account_base_url() -> Optional[str]:
    return getenv(DMW_STUB_DIEM_ACCOUNT_BASE_URL)


def dmw_stub_server() -> Dict[str, Any]:
    return {
        k: v
        for k, v in {
            "host": dmw_stub_bind_host(),
            "port": dmw_stub_bind_port(),
            "base_url": dmw_stub_diem_account_base_url(),
        }.items()
        if v
    }


def dmw_stub_bind_host() -> Optional[str]:
    return getenv(DMW_STUB_BIND_HOST)


def dmw_stub_bind_port() -> Optional[int]:
    port = getenv(DMW_STUB_BIND_PORT)
    if port is not None:
        return int(port)


def target_url() -> str:
    return environ[TARGET_URL]


def is_self_check() -> bool:
    return getenv(SELF_CHECK) is not None


def should_test_debug_api() -> bool:
    return getenv(TEST_DEBUG_API) is not None
