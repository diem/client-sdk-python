# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module provides test suites built for verifying the compatibility of a wallet implementing
[Diem Transactions Specification](https://github.com/diem/diem/tree/main/specifications/transactions).

To test Diem payment transactions integration, the target wallet application should implement [MiniWallet API](https://diem.github.io/client-sdk-python/mini-wallet-api-spec.html), or implementing [MiniWallet API](https://diem.github.io/client-sdk-python/mini-wallet-api-spec.html) as a new http server and proxy the functions to the target wallet application APIs.

HTTP requests from the test suite will have the following custom HTTP headers:

1. X-Test-Case: the current running test case full name; it is `PYTEST_CURRENT_TEST` environment variable value, see [pytest document](https://docs.pytest.org/en/latest/example/simple.html#pytest-current-test-environment-variable) for more details.

Before any tests started, a stub wallet application is configured and started as counterparty wallet application of the target wallet application for wallet to wallet payment tests.

The stub wallet application also implements [MiniWallet API](https://diem.github.io/client-sdk-python/mini-wallet-api-spec.html).

When a test finished, the target wallet application's account events endpoint (`GET /accounts/{account_id}/events`) will be called and the response will be dumped into logs. As the endpoint is optional to implement, we ignore errors and log nothing when calling the endpoint failed.
"""
