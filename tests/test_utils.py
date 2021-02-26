# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import diem_types, utils, InvalidAccountAddressError, InvalidSubAddressError, jsonrpc

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


def test_currency_code():
    ccode = utils.currency_code("XUS")
    assert isinstance(ccode, diem_types.TypeTag)

    code = utils.type_tag_to_str(ccode)
    assert code == "XUS"

    with pytest.raises(TypeError):
        utils.currency_code(False)

    with pytest.raises(TypeError):
        utils.type_tag_to_str(False)


def test_decode_transaction_script():
    script_bytes = "e001a11ceb0b010000000701000202020403061004160205181d0735600895011000000001010000020001000003020301010004010300010501060c0108000506080005030a020a020005060c05030a020a020109000b4469656d4163636f756e741257697468647261774361706162696c6974791b657874726163745f77697468647261775f6361706162696c697479087061795f66726f6d1b726573746f72655f77697468647261775f6361706162696c69747900000000000000000000000000000001010104010c0b0011000c050e050a010a020b030b0438000b05110202010700000000000000000000000000000001035855530358555300040393e341892c775c38fd524757d641f0a20100e1f5050000000004000400"

    script_call = utils.decode_transaction_script(script_bytes)
    assert type(script_call).__name__ == "ScriptCall__PeerToPeerWithMetadata"
    assert script_call.amount == 100_000_000

    script_call = utils.decode_transaction_script(jsonrpc.TransactionData(script_bytes=script_bytes))
    assert type(script_call).__name__ == "ScriptCall__PeerToPeerWithMetadata"
    assert script_call.amount == 100_000_000

    script_call = utils.decode_transaction_script(
        jsonrpc.Transaction(transaction=jsonrpc.TransactionData(script_bytes=script_bytes))
    )
    assert type(script_call).__name__ == "ScriptCall__PeerToPeerWithMetadata"
    assert script_call.amount == 100_000_000

    with pytest.raises(TypeError):
        utils.decode_transaction_script(False)


def test_balance():
    account = jsonrpc.Account(
        balances=[
            jsonrpc.Amount(amount=32, currency="XUS"),
            jsonrpc.Amount(amount=33, currency="XDX"),
        ]
    )
    assert utils.balance(account, "XUS") == 32
    assert utils.balance(account, "XDX") == 33
    assert utils.balance(account, "unknown") == 0


def test_to_snake():
    assert utils.to_snake("AbcEfg") == "abc_efg"
    assert utils.to_snake("ABC") == "a_b_c"
    assert utils.to_snake(TypeError) == "type_error"
    assert utils.to_snake(TypeError("hello")) == "type_error"


def test_hex():
    assert utils.hex(None) == ""
    assert utils.hex(b"abcd") == "61626364"
