# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0


from libra import utils, InvalidAccountAddressError
import pytest


def test_account_address():
    with pytest.raises(InvalidAccountAddressError):
        utils.account_address(bytes.fromhex("aaaa"))

    with pytest.raises(InvalidAccountAddressError):
        utils.account_address("aaaa")

    with pytest.raises(InvalidAccountAddressError):
        utils.account_address("0000000000000000000000000a550c1x")

    assert utils.account_address("0000000000000000000000000a550c18")
