# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
from diem import identifier, utils, InvalidSubAddressError, InvalidAccountAddressError


test_onchain_address = "f72589b71ff4f8d139674a3f7369c69b"
test_sub_address = "cf64428bdeb62af2"
none_sub_address = None
zero_sub_address = "00" * 8


@pytest.fixture(
    scope="module",
    params=[
        (
            "dm",
            "dm1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqqd8p9cq",
            "dm1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4us2vfufk",
        ),
        (
            "tdm",
            "tdm1p7ujcndcl7nudzwt8fglhx6wxnvqqqqqqqqqqqqqv88j4s",
            "tdm1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4ustv0tyx",
        ),
    ],
)
def hrp_addresses(request):
    return request.param


def test_identifier_hrps():
    assert identifier.HRPS == {1: "dm", 2: "tdm", 3: "tdm", 4: "tdm"}


def test_encode_addr_success(hrp_addresses):
    hrp, enocded_addr_with_none_subaddr, enocded_addr_with_subaddr = hrp_addresses

    # test with none sub_address
    enocded_addr = identifier.encode_account(test_onchain_address, None, hrp)
    assert enocded_addr == enocded_addr_with_none_subaddr

    # even with zero sub_address, expected should not change from above
    enocded_addr = identifier.encode_account(test_onchain_address, zero_sub_address, hrp)
    assert enocded_addr == enocded_addr_with_none_subaddr

    # test with some subaddress
    enocded_addr = identifier.encode_account(test_onchain_address, test_sub_address, hrp)
    assert enocded_addr == enocded_addr_with_subaddr

    # accept AccountAddress and bytes sub-address as params too
    enocded_addr = identifier.encode_account(
        utils.account_address(test_onchain_address), utils.sub_address(test_sub_address), hrp
    )
    assert enocded_addr == enocded_addr_with_subaddr


def test_encode_addr_fail(hrp_addresses):
    hrp = hrp_addresses[0]
    # wrong subadress (length should be 8 bytes)
    with pytest.raises(InvalidSubAddressError):
        identifier.encode_account(test_onchain_address, test_sub_address[:-2], hrp)

    # wrong address (length should be 16 bytes)
    with pytest.raises(InvalidAccountAddressError):
        identifier.encode_account(test_onchain_address + "ff", test_sub_address[:-2], hrp)


def test_decode_addr_success(hrp_addresses):
    hrp, enocded_addr_with_none_subaddr, enocded_addr_with_subaddr = hrp_addresses
    # test enocded_addr_with_none_subaddr
    addr, subaddr = identifier.decode_account(enocded_addr_with_none_subaddr, hrp)
    assert addr.to_hex() == test_onchain_address
    assert subaddr is None

    # test enocded_addr_with_subaddr
    addr, subaddr = identifier.decode_account(enocded_addr_with_subaddr, hrp)
    assert addr.to_hex() == test_onchain_address
    assert subaddr.hex() == test_sub_address


def test_encode_decode_with_random_hrp():
    # test with none sub_address
    id = identifier.encode_account(test_onchain_address, None, "abc")
    addr, sub = identifier.decode_account(id, "abc")
    assert addr.to_hex() == test_onchain_address
    assert sub is None


def test_decode_addr_fail(hrp_addresses):
    hrp, enocded_addr_with_none_subaddr, enocded_addr_with_subaddr = hrp_addresses

    # fail to decode invalid hrp
    invalid_hrp_encoded_address = "btc1p7ujcndcl7nudzwt8fglhx6wxn08kgs5tm6mz4usw5p72t"
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_hrp_encoded_address, hrp)

    # fail to decode invalid "expected" hrp
    with pytest.raises(ValueError):
        identifier.decode_account(enocded_addr_with_none_subaddr, "xdm")

    # fail to decode invalid version
    invalid_version_encoded_address = enocded_addr_with_none_subaddr.replace("1p7", "1q7")  # p (1) -> q (2)
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_version_encoded_address, hrp)

    # fail to decode due to checksum error
    invalid_checksum_encoded_address = enocded_addr_with_none_subaddr.replace("d8p9cq", "d8p9c7").replace(
        "v88j4s", "v88j4q"
    )
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_checksum_encoded_address, hrp)

    # fail to decode mixed case per BIP 173
    mixedcase_encoded_address = enocded_addr_with_none_subaddr.replace("qqqqqqqqqqqqq", "qqQqqqqqqqqqq")
    with pytest.raises(ValueError):
        identifier.decode_account(mixedcase_encoded_address, hrp)

    # fail to decode shorter payload
    short_encoded_address = enocded_addr_with_none_subaddr.replace("qqqqqqqqqqqqq", "qqqqqqqqqqq")
    with pytest.raises(ValueError):
        identifier.decode_account(short_encoded_address, hrp)

    # fail to decode larger payload
    large_encoded_address = enocded_addr_with_none_subaddr.replace("qqqqqqqqqqqqq", "qqqqqqqqqqqqqq")
    with pytest.raises(ValueError):
        identifier.decode_account(large_encoded_address, hrp)

    # fail to decode invalid separator
    invalid_separator_encoded_address = enocded_addr_with_none_subaddr.replace("1p7", "0p7")
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_separator_encoded_address, hrp)

    # fail to decode invalid character
    invalid_char_encoded_address = enocded_addr_with_none_subaddr.replace("1p7", "1pb")
    with pytest.raises(ValueError):
        identifier.decode_account(invalid_char_encoded_address, hrp)


def test_intent_identifier(hrp_addresses):
    hrp, enocded_addr_with_none_subaddr, enocded_addr_with_subaddr = hrp_addresses
    account_id = identifier.encode_account(test_onchain_address, None, hrp)
    intent_id = identifier.encode_intent(account_id, "XUS", 123)
    assert intent_id == "diem://%s?c=%s&am=%d" % (enocded_addr_with_none_subaddr, "XUS", 123)

    intent = identifier.decode_intent(intent_id, hrp)
    assert intent.account_address == utils.account_address(test_onchain_address)
    assert intent.account_address_bytes.hex() == test_onchain_address
    assert intent.sub_address is None
    assert intent.currency_code == "XUS"
    assert intent.amount == 123

    assert account_id == intent.account_id


def test_intent_identifier_with_sub_address(hrp_addresses):
    hrp, enocded_addr_with_none_subaddr, enocded_addr_with_subaddr = hrp_addresses
    account_id = identifier.encode_account(test_onchain_address, test_sub_address, hrp)
    intent_id = identifier.encode_intent(account_id, "XUS", 123)
    assert intent_id == "diem://%s?c=%s&am=%d" % (enocded_addr_with_subaddr, "XUS", 123)

    intent = identifier.decode_intent(intent_id, hrp)
    assert intent.account_address_bytes.hex() == test_onchain_address
    assert intent.sub_address == bytes.fromhex(test_sub_address)
    assert intent.currency_code == "XUS"
    assert intent.amount == 123


def test_intent_identifier_decode_errors(hrp_addresses):
    hrp, enocded_addr_with_none_subaddr, enocded_addr_with_subaddr = hrp_addresses
    # amount is not int
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?c=XUS&am=str" % (enocded_addr_with_none_subaddr), hrp)

    # amount not exist
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?c=XUS" % (enocded_addr_with_none_subaddr), hrp)

    # too many amount
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?c=XUS&am=2&am=3" % (enocded_addr_with_none_subaddr), hrp)

    # amount is none
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?c=XUS&am=" % (enocded_addr_with_none_subaddr), hrp)

    # currency code not exist
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?am=2" % (enocded_addr_with_none_subaddr), hrp)

    # scheme not match
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("hello://%s?am=2&c=XUS" % (enocded_addr_with_none_subaddr), hrp)

    # hrp not match
    with pytest.raises(identifier.InvalidIntentIdentifierError):
        identifier.decode_intent("diem://%s?am=2&c=XUS" % (enocded_addr_with_none_subaddr), "xdm")
