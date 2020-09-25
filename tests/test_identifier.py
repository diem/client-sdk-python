# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
from libra import AccountIdentifier


test_onchain_address = "f72589b71ff4f8d139674a3f7369c69b"
test_sub_address = "cf64428bdeb62af2"
none_sub_address = None
zero_sub_address = "00" * 8

# These are the encoded addr values for the above test address & subaddress
enocded_addr_with_none_subaddr = "lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqqflf8ma"
enocded_addr_with_subaddr = "lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"


def test_encode_addr_success():
    # test with none sub_address
    enocded_addr = AccountIdentifier.encode(test_onchain_address, None, "lbr")
    assert enocded_addr == enocded_addr_with_none_subaddr

    # even with zero sub_address, expected should not change from above
    enocded_addr = AccountIdentifier.encode(test_onchain_address, zero_sub_address, "lbr")
    assert enocded_addr == enocded_addr_with_none_subaddr

    # test with some subaddress
    enocded_addr = AccountIdentifier.encode(test_onchain_address, test_sub_address, "lbr")
    assert enocded_addr == enocded_addr_with_subaddr


def test_encode_addr_fail():
    # wrong hrp
    with pytest.raises(ValueError):
        AccountIdentifier.encode(test_onchain_address, None, "btc")

    # wrong subadress (length should be 8 bytes)
    with pytest.raises(ValueError):
        AccountIdentifier.encode(test_onchain_address, test_sub_address[:-2], "lbr")

    # wrong address (length should be 16 bytes)
    with pytest.raises(ValueError):
        AccountIdentifier.encode(test_onchain_address + "ff", test_sub_address[:-2], "lbr")


def test_decode_addr_success():
    # test enocded_addr_with_none_subaddr
    addr, subaddr = AccountIdentifier.decode(enocded_addr_with_none_subaddr, "lbr")
    assert addr == test_onchain_address
    assert subaddr is None

    # test enocded_addr_with_subaddr
    addr, subaddr = AccountIdentifier.decode(enocded_addr_with_subaddr, "lbr")
    assert addr == test_onchain_address
    assert subaddr == test_sub_address


def test_decode_addr_fail():
    # fail to decode invalid hrp
    invalid_hrp_encoded_address = "btc1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"
    with pytest.raises(ValueError):
        AccountIdentifier.decode(invalid_hrp_encoded_address, "lbr")

    # fail to decode invalid "expected" hrp
    with pytest.raises(ValueError):
        AccountIdentifier.decode("lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t", "tlb")

    # fail to decode invalid version
    invalid_version_encoded_address = "lbr1q7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"  # v = 0
    with pytest.raises(ValueError):
        AccountIdentifier.decode(invalid_version_encoded_address, "lbr")

    # fail to decode due to checksum error
    invalid_checksum_encoded_address = (
        "lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72p"  # change last char from t to p
    )
    with pytest.raises(ValueError):
        AccountIdentifier.decode(invalid_checksum_encoded_address, "lbr")

    # fail to decode mixed case per BIP 173
    mixedcase_encoded_address = "LbR1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5P72T"  # some uppercase
    with pytest.raises(ValueError):
        AccountIdentifier.decode(mixedcase_encoded_address)

    # fail to decode shorter payload
    short_encoded_address = "lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv"  # sample 23 bytes encoded
    with pytest.raises(ValueError):
        AccountIdentifier.decode(short_encoded_address, "lbr")

    # fail to decode larger payload
    large_encoded_address = "lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4us4g3ysw8a"  # sample 25 bytes encoded
    with pytest.raises(ValueError):
        AccountIdentifier.decode(large_encoded_address, "lbr")

    # fail to decode invalid separator
    invalid_separator_encoded_address = "lbr2p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"  # separator = 2
    with pytest.raises(ValueError):
        AccountIdentifier.decode(invalid_separator_encoded_address, "lbr")

    # fail to decode invalid character
    invalid_char_encoded_address = "lbr1pbujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"  # add b char
    with pytest.raises(ValueError):
        AccountIdentifier.decode(invalid_char_encoded_address, "lbr")
