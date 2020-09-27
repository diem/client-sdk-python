# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0


from libra import libra_types, utils, InvalidAccountAddressError, InvalidSubAddressError

import pytest


def test_account_address():
    with pytest.raises(InvalidAccountAddressError):
        utils.account_address(bytes.fromhex("aaaa"))

    with pytest.raises(InvalidAccountAddressError):
        utils.account_address("aaaa")

    with pytest.raises(InvalidAccountAddressError):
        utils.account_address("0000000000000000000000000a550c1x")

    valid_address = "0000000000000000000000000a550c18"
    address = utils.account_address(valid_address)
    assert address
    assert utils.account_address(address) == address
    assert utils.account_address(bytes.fromhex(valid_address)) == address


def test_sub_address():
    with pytest.raises(InvalidSubAddressError):
        utils.sub_address(bytes.fromhex("aa"))

    assert utils.sub_address(bytes.fromhex("aaaaaaaaaaaaaaaa")) is not None

    with pytest.raises(InvalidSubAddressError):
        utils.sub_address("aa")

    sub_address = utils.sub_address("aaaaaaaaaaaaaaaa")
    assert sub_address is not None
    assert isinstance(sub_address, bytes)
