# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0


from libra import utils, InvalidAccountAddressError, InvalidSubAddressError
import pytest


def test_account_address():
    with pytest.raises(InvalidAccountAddressError):
        utils.account_address(bytes.fromhex("aaaa"))

    with pytest.raises(InvalidAccountAddressError):
        utils.account_address("aaaa")

    with pytest.raises(InvalidAccountAddressError):
        utils.account_address("0000000000000000000000000a550c1x")

    assert utils.account_address("0000000000000000000000000a550c18")


def test_sub_address():
    with pytest.raises(InvalidSubAddressError):
        utils.sub_address(bytes.fromhex("aa"))

    assert utils.sub_address(bytes.fromhex("aaaaaaaaaaaaaaaa")) is not None

    with pytest.raises(InvalidSubAddressError):
        utils.sub_address("aa")

    sub_address = utils.sub_address("aaaaaaaaaaaaaaaa")
    assert sub_address is not None
    assert isinstance(sub_address, bytes)
