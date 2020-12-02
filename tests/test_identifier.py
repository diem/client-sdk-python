# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
from diem import identifier, utils, InvalidSubAddressError, InvalidAccountAddressError


test_onchain_address = "f72589b71ff4f8d139674a3f7369c69b"
test_sub_address = "cf64428bdeb62af2"
none_sub_address = None
zero_sub_address = "00" * 8

# These are the encoded addr values for the above test address & subaddress
enocded_addr_with_none_subaddr = "lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqqflf8ma"
enocded_addr_with_subaddr = "lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"


def test_identifier_hrps():
    assert identifier.HRPS == {1: "lbr", 2: "tlb", 3: "tlb", 4: "tlb", 19: "plb"}


def test_encode_addr_success():
    # test with none sub_address
    enocded_addr = identifier.encode_account(test_onchain_address, None, "lbr")
    assert enocded_addr == enocded_addr_with_none_subaddr

    # even with zero sub_address, expected should not change from above
    enocded_addr = identifier.encode_account(test_onchain_address, zero_sub_address, "lbr")
    assert enocded_addr == enocded_addr_with_none_subaddr

    # test with some subaddress
    enocded_addr = identifier.encode_account(test_onchain_address, test_sub_address, "lbr")
    assert enocded_addr == enocded_addr_with_subaddr

    # accept AccountAddress and bytes sub-address as params too
    enocded_addr = identifier.encode_account(
        utils.account_address(test_onchain_address), utils.sub_address(test_sub_address), "lbr"
    )
    assert enocded_addr == enocded_addr_with_subaddr


def test_encode_addr_fail():
    # wrong subadress (length should be 8 bytes)
    with pytest.raises(InvalidSubAddressError):
        identifier.encode_account(test_onchain_address, test_sub_address[:-2], "lbr")

    # wrong address (length should be 16 bytes)
    with pytest.raises(InvalidAccountAddressError):
        identifier.encode_account(test_onchain_address + "ff", test_sub_address[:-2], "lbr")


def test_decode_addr_success():
    # test enocded_addr_with_none_subaddr
    addr, subaddr = identifier.decode_account(enocded_addr_with_none_subaddr, "lbr")
    assert addr.to_hex() == test_onchain_address
    assert subaddr is None

    # test enocded_addr_with_subaddr
    addr, subaddr = identifier.decode_account(enocded_addr_with_subaddr, "lbr")
    assert addr.to_hex() == test_onchain_address
    assert subaddr.hex() == test_sub_address


def test_encode_decode_with_random_hrp():
    # test with none sub_address
    id = identifier.encode_account(test_onchain_address, None, "abc")
    addr, sub = identifier.decode_account(id, "abc")
    assert addr.to_hex() == test_onchain_address
    assert sub is None


def test_decode_addr_fail():
    # fail to decode invalid hrp
    invalid_hrp_encoded_address = "btc1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_hrp_encoded_address, "lbr")

    # fail to decode invalid "expected" hrp
    with pytest.raises(ValueError):
        identifier.decode_account("lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t", "tlb")

    # fail to decode invalid version
    invalid_version_encoded_address = "lbr1q7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"  # v = 0
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_version_encoded_address, "lbr")

    # fail to decode due to checksum error
    invalid_checksum_encoded_address = (
        "lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72p"  # change last char from t to p
    )
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_checksum_encoded_address, "lbr")

    # fail to decode mixed case per BIP 173
    mixedcase_encoded_address = "LbR1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5P72T"  # some uppercase
    with pytest.raises(ValueError):
        identifier.decode_account(mixedcase_encoded_address, "lbr")

    # fail to decode shorter payload
    short_encoded_address = "lbr1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqelu3xv"  # sample 23 bytes encoded
    with pytest.raises(ValueError):
        identifier.decode_account(short_encoded_address, "lbr")

    # fail to decode larger payload
    large_encoded_address = "lbr1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4us4g3ysw8a"  # sample 25 bytes encoded
    with pytest.raises(ValueError):
        identifier.decode_account(large_encoded_address, "lbr")

    # fail to decode invalid separator
    invalid_separator_encoded_address = "lbr2p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"  # separator = 2
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_separator_encoded_address, "lbr")

    # fail to decode invalid character
    invalid_char_encoded_address = "lbr1pbujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"  # add b char
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_char_encoded_address, "lbr")


def test_intent_identifier():
    account_id = identifier.encode_account(test_onchain_address, None, "lbr")
    intent_id = identifier.encode_intent(account_id, "Coin1", 123)
    assert intent_id == "diem://%s?c=%s&am=%d" % (enocded_addr_with_none_subaddr, "Coin1", 123)

    intent = identifier.decode_intent(intent_id, "lbr")
    assert intent.account_address == utils.account_address(test_onchain_address)
    assert intent.account_address_bytes.hex() == test_onchain_address
    assert intent.sub_address is None
    assert intent.currency_code == "Coin1"
    assert intent.amount == 123


def test_intent_identifier_with_sub_address():
    account_id = identifier.encode_account(test_onchain_address, test_sub_address, "lbr")
    intent_id = identifier.encode_intent(account_id, "Coin1", 123)
    assert intent_id == "diem://%s?c=%s&am=%d" % (enocded_addr_with_subaddr, "Coin1", 123)

    intent = identifier.decode_intent(intent_id, "lbr")
    assert intent.account_address_bytes.hex() == test_onchain_address
    assert intent.sub_address == bytes.fromhex(test_sub_address)
    assert intent.currency_code == "Coin1"
    assert intent.amount == 123


def test_intent_identifier_decode_errors():
    # amount is not int
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?c=Coin1&am=str" % (enocded_addr_with_none_subaddr), "lbr")

    # amount not exist
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?c=Coin1" % (enocded_addr_with_none_subaddr), "lbr")

    # too many amount
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?c=Coin1&am=2&am=3" % (enocded_addr_with_none_subaddr), "lbr")

    # amount is none
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?c=Coin1&am=" % (enocded_addr_with_none_subaddr), "lbr")

    # currency code not exist
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?am=2" % (enocded_addr_with_none_subaddr), "lbr")

    # scheme not match
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("hello://%s?am=2&c=Coin1" % (enocded_addr_with_none_subaddr), "lbr")

    # hrp not match
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?am=2&c=Coin1" % (enocded_addr_with_none_subaddr), "tlb")
