# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from os import getenv, environ


TARGET_URL: str = "DMW_TEST_TARGET"
TEST_DEBUG_API: str = "DMW_TEST_DEBUG_API"
SELF_CHECK: str = "DMW_SELF_CHECK"


def target_url() -> str:
    return environ[TARGET_URL]


def is_self_check() -> bool:
    return getenv(SELF_CHECK) is not None


def should_test_debug_api() -> bool:
    return getenv(TEST_DEBUG_API) is not None
