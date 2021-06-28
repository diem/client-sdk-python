# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import offchain


def test_is_under_the_threshold():
    assert offchain.client._is_under_the_threshold(2, 0.2, 1)
    assert offchain.client._is_under_the_threshold(2, 0.2, 5)
    assert not offchain.client._is_under_the_threshold(2, 0.2, 6)
    assert not offchain.client._is_under_the_threshold(2, 0.2, 10)


def test_filter_supported_currency_codes():
    assert ["XUS", "XDX"] == offchain.client._filter_supported_currency_codes(None, ["XUS", "XDX"])
    assert ["XUS"] == offchain.client._filter_supported_currency_codes(["XUS"], ["XUS", "XDX"])
    assert ["XDX"] == offchain.client._filter_supported_currency_codes(None, ["XDX"])
    assert [] == offchain.client._filter_supported_currency_codes(["XUS"], ["XDX"])
