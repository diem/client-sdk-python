# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import identifier, utils, testnet
from diem.testing import LocalAccount
import pytest


def test_from_private_key_hex():
    account = LocalAccount.generate()
    hex_key = utils.private_key_bytes(account.private_key).hex()
    new_account = LocalAccount.from_private_key_hex(hex_key)
    assert utils.private_key_bytes(new_account.private_key).hex() == hex_key


def test_from_and_to_dict():
    config = {
        "private_key": "ab70ae3aa603641f049a3356927d0ba836f775e862f559073a6281782479fd1e",
        "compliance_key": "f75b74a94250bda7abfab2045205e05c56e5dcba24ecea6aff75aac9463cdc2f",
        "hrp": "tdm",
        "txn_gas_currency_code": "XDX",
        "txn_max_gas_amount": 1000000,
        "txn_gas_unit_price": 0,
        "txn_expire_duration_secs": 30,
    }
    account = LocalAccount.from_dict(config)
    assert account.to_dict() == config


def test_generate_keys():
    account = LocalAccount()
    sig1 = account.private_key.sign(b"test")
    sig2 = account.compliance_key.sign(b"test")

    load_account = LocalAccount.from_dict(account.to_dict())
    assert sig1 == load_account.private_key.sign(b"test")
    assert sig2 == load_account.compliance_key.sign(b"test")


def test_from_dict_generate_keys():
    account = LocalAccount.from_dict({})
    assert account
    assert account.private_key
    assert account.compliance_key


def test_account_identifier():
    account = LocalAccount()
    assert account.account_identifier() == identifier.encode_account(account.account_address, None, account.hrp)
    subaddress = identifier.gen_subaddress()
    assert account.account_identifier(subaddress) == identifier.encode_account(
        account.account_address, subaddress, account.hrp
    )
    assert account.account_identifier(subaddress.hex()) == identifier.encode_account(
        account.account_address, subaddress, account.hrp
    )


def test_decode_account_identifier():
    account = LocalAccount()

    id1 = account.account_identifier()
    address, subaddress = account.decode_account_identifier(id1)
    assert address == account.account_address
    assert subaddress is None

    subaddress = identifier.gen_subaddress()
    id2 = account.account_identifier(subaddress)
    address, subaddress = account.decode_account_identifier(id2)
    assert address == account.account_address
    assert subaddress == subaddress


@pytest.mark.asyncio
async def test_gen_child_vasp():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)
    account = LocalAccount(
        hrp=identifier.DM,
        txn_gas_currency_code="XUS",
        txn_max_gas_amount=1_000_001,
        txn_gas_unit_price=1,
        txn_expire_duration_secs=60,
    )
    await faucet.mint(account.auth_key.hex(), 10_000_000, "XUS")

    child_account = await account.gen_child_vasp(client, 1, "XUS")
    assert child_account.hrp == account.hrp
    assert child_account.txn_gas_currency_code == account.txn_gas_currency_code
    assert child_account.txn_max_gas_amount == account.txn_max_gas_amount
    assert child_account.txn_gas_unit_price == account.txn_gas_unit_price
    assert child_account.txn_expire_duration_secs == account.txn_expire_duration_secs
    assert child_account.compliance_key == account.compliance_key
    assert child_account.private_key != account.private_key
    child_diem_account = await client.must_get_account(child_account.account_address)
    assert child_diem_account.role.type == "child_vasp"
