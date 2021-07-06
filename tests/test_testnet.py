# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import (
    jsonrpc,
    diem_types,
    stdlib,
    testnet,
    utils,
    InvalidAccountAddressError,
    TREASURY_ADDRESS,
    ROOT_ADDRESS,
)
from diem.testing import LocalAccount

import time
import pytest


def test_get_metadata():
    client = testnet.create_client()
    metadata = client.get_metadata()
    assert metadata is not None
    assert isinstance(metadata, jsonrpc.Metadata)
    assert metadata.chain_id == testnet.CHAIN_ID.value
    assert metadata.version is not None
    assert metadata.timestamp is not None


def test_get_metadata_by_version():
    client = testnet.create_client()
    metadata = client.get_metadata(1)
    assert metadata is not None
    assert isinstance(metadata, jsonrpc.Metadata)
    assert metadata.chain_id == testnet.CHAIN_ID.value
    assert metadata.version == 1
    assert metadata.timestamp is not None

    # this is unexpected, will be updated to return None later
    with pytest.raises(jsonrpc.JsonRpcError):
        metadata = client.get_metadata(1999999999999)


def test_get_currencies():
    client = testnet.create_client()
    currencies = client.get_currencies()
    assert currencies is not None
    assert isinstance(currencies, list)
    assert len(currencies) > 0

    lbr = next(filter(lambda curr: curr.code == testnet.TEST_CURRENCY_CODE, currencies))
    assert lbr is not None
    assert isinstance(lbr, jsonrpc.CurrencyInfo)


def test_get_account():
    client = testnet.create_client()
    account = client.get_account(testnet.DESIGNATED_DEALER_ADDRESS)
    assert account is not None
    assert isinstance(account, jsonrpc.Account)
    assert account.role is not None
    assert account.role.type == jsonrpc.ACCOUNT_ROLE_DESIGNATED_DEALER


def test_get_account_by_hex_encoded_account_address():
    client = testnet.create_client()
    account = client.get_account(TREASURY_ADDRESS)
    assert account is not None
    assert isinstance(account, jsonrpc.Account)
    assert account.role is not None


def test_get_account_by_invalid_hex_encoded_account_address():
    client = testnet.create_client()
    with pytest.raises(InvalidAccountAddressError):
        client.get_account(TREASURY_ADDRESS + "invalid")


def test_get_account_not_exist():
    local_account = LocalAccount.generate()
    client = testnet.create_client()
    account = client.get_account(local_account.account_address)
    assert account is None


def test_get_account_sequence():
    client = testnet.create_client()
    seq = client.get_account_sequence(testnet.DESIGNATED_DEALER_ADDRESS)
    assert isinstance(seq, int)
    assert seq > 0

    local = LocalAccount.generate()
    with pytest.raises(jsonrpc.AccountNotFoundError):
        client.get_account_sequence(local.account_address)


def test_get_account_transaction():
    client = testnet.create_client()
    txn = client.get_account_transaction(testnet.DESIGNATED_DEALER_ADDRESS, 0)
    assert txn is not None
    assert isinstance(txn, jsonrpc.Transaction)
    assert txn.version > 0
    assert txn.hash is not None
    assert len(txn.events) == 0


def test_get_account_transaction_not_exist():
    client = testnet.create_client()
    txn = client.get_account_transaction(ROOT_ADDRESS, 9000000000000000)
    assert txn is None


def test_get_account_transaction_by_hex_encoded_account_address():
    client = testnet.create_client()
    txn = client.get_account_transaction(testnet.DESIGNATED_DEALER_ADDRESS.to_hex(), 0)
    assert txn is not None
    assert isinstance(txn, jsonrpc.Transaction)
    assert txn.version > 0
    assert txn.hash is not None
    assert len(txn.events) == 0


def test_get_account_transaction_include_events():
    client = testnet.create_client()
    account = testnet.gen_account(client, base_url="http://baseurl")

    txn = client.get_account_transaction(account.account_address, 0, include_events=True)
    assert txn is not None
    assert isinstance(txn, jsonrpc.Transaction)
    assert len(txn.events) > 0


def test_get_account_transactions():
    client = testnet.create_client()
    txns = client.get_account_transactions(testnet.DESIGNATED_DEALER_ADDRESS, 0, 1)
    assert txns is not None
    assert isinstance(txns, list)

    txn = txns[0]
    assert isinstance(txn, jsonrpc.Transaction)
    assert txn.version > 0
    assert txn.hash is not None
    assert len(txn.events) == 0


def test_get_account_transactions_not_exist():
    client = testnet.create_client()
    txn = client.get_account_transactions(ROOT_ADDRESS, 9000000000000000, 1)
    assert txn == []


def test_get_account_transactions_by_hex_encoded_account_address():
    client = testnet.create_client()
    txns = client.get_account_transactions(testnet.DESIGNATED_DEALER_ADDRESS.to_hex(), 0, 1)
    assert txns is not None
    assert isinstance(txns, list)

    txn = txns[0]
    assert isinstance(txn, jsonrpc.Transaction)
    assert txn.version > 0
    assert txn.hash is not None
    assert len(txn.events) == 0


def test_get_account_transactions_with_events():
    client = testnet.create_client()
    account = testnet.gen_account(client, base_url="url")
    txns = client.get_account_transactions(account.account_address, 0, 1, include_events=True)
    assert txns is not None
    assert isinstance(txns, list)

    txn = txns[0]
    assert isinstance(txn, jsonrpc.Transaction)
    assert len(txn.events) > 0


def test_get_transactions():
    client = testnet.create_client()
    txns = client.get_transactions(1, 1)
    assert txns is not None
    assert isinstance(txns, list)

    txn = txns[0]
    assert isinstance(txn, jsonrpc.Transaction)
    assert txn.version == 1
    assert txn.hash is not None


def test_get_events():
    client = testnet.create_client()
    account = client.get_account(testnet.DESIGNATED_DEALER_ADDRESS)
    events = client.get_events(account.sent_events_key, 0, 1)
    assert events is not None
    assert isinstance(events, list)

    event = events[0]
    assert isinstance(event, jsonrpc.Event)
    assert event.key == account.sent_events_key
    assert event.data is not None
    assert event.data.type == jsonrpc.EVENT_DATA_SENT_PAYMENT


def test_get_state_proof():
    client = testnet.create_client()
    state_proof = client.get_state_proof(1)
    assert state_proof is not None
    assert isinstance(state_proof, jsonrpc.StateProof)
    # todo: decode ledger_info and validate version


def test_get_last_known_state():
    client = testnet.create_client()
    metadata = client.get_metadata()
    assert metadata is not None
    state = client.get_last_known_state()
    assert state is not None

    assert metadata.chain_id == state.chain_id
    assert metadata.version == state.version
    assert metadata.timestamp == state.timestamp_usecs


def test_get_account_state_with_proof():
    client = testnet.create_client()
    state_proof = client.get_account_state_with_proof(testnet.DESIGNATED_DEALER_ADDRESS)
    assert state_proof is not None
    assert isinstance(state_proof, jsonrpc.AccountStateWithProof)
    assert state_proof.version == client.get_last_known_state().version


def test_handle_stale_response_error():
    client = testnet.create_client()
    last = client.get_metadata().version
    for i in range(0, 20):
        metadata = client.get_metadata()
        assert metadata.version >= last
        assert client.get_last_known_state().version == metadata.version
        last = metadata.version


def test_submit_create_child_vasp():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    parent_vasp = faucet.gen_account()
    child_vasp = LocalAccount.generate()
    signed_txn = create_child_vasp_txn(parent_vasp, child_vasp)

    client.submit(signed_txn)

    executed_txn = client.wait_for_transaction(signed_txn)
    assert executed_txn is not None
    assert isinstance(executed_txn, jsonrpc.Transaction)
    assert executed_txn.vm_status.type == jsonrpc.VM_STATUS_EXECUTED

    # wait for transaction by signed txn hex string
    signed_txn_hex = signed_txn.bcs_serialize().hex()
    executed_txn = client.wait_for_transaction(signed_txn_hex)
    assert executed_txn is not None
    assert isinstance(executed_txn, jsonrpc.Transaction)
    assert executed_txn.vm_status.type == jsonrpc.VM_STATUS_EXECUTED
    # should include events
    assert len(executed_txn.events) > 0


def test_submit_failed():
    client = testnet.create_client()

    with pytest.raises(jsonrpc.JsonRpcError):
        client.submit("invalid txn")


def test_submit_ignores_stale_resposne_error():
    client = testnet.create_client()
    account = testnet.gen_account(client)
    payload = stdlib.encode_rotate_dual_attestation_info_script_function(
        new_url="http://localhost".encode("utf-8"), new_key=account.compliance_public_key_bytes
    )
    txn = account.create_signed_txn(0, payload)
    state = client.get_last_known_state()
    client._last_known_server_state.version = state.version + 1_000_000_000
    client.submit(txn)
    client._last_known_server_state = state
    assert client.wait_for_transaction(txn)


def test_wait_for_transaction_hash_mismatched_and_execution_failed():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    parent_vasp = faucet.gen_account()
    # parent vasp as child, invalid transaction
    signed_txn = create_child_vasp_txn(parent_vasp, parent_vasp)
    client.submit(signed_txn)

    txn = signed_txn.raw_txn
    with pytest.raises(jsonrpc.TransactionHashMismatchError):
        client.wait_for_transaction2(txn.sender, txn.sequence_number, txn.expiration_timestamp_secs, "mismatched hash")

    with pytest.raises(jsonrpc.TransactionExecutionFailed):
        client.wait_for_transaction(signed_txn)


def test_wait_for_transaction_timeout_and_expire():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    parent_vasp = faucet.gen_account()

    with pytest.raises(jsonrpc.TransactionExpired):
        client.wait_for_transaction2(parent_vasp.account_address, 1, time.time() + 0.2, "hash")

    with pytest.raises(jsonrpc.WaitForTransactionTimeout):
        client.wait_for_transaction2(parent_vasp.account_address, 1, time.time() + 5, "hash", 0.1)


def test_get_parent_vasp_account():
    client = testnet.create_client()
    faucet = testnet.Faucet(client)

    parent_vasp = faucet.gen_account()
    child_vasp = LocalAccount.generate()
    signed_txn = create_child_vasp_txn(parent_vasp, child_vasp)

    client.submit(signed_txn)
    client.wait_for_transaction(signed_txn)

    account = client.get_parent_vasp_account(child_vasp.account_address)

    expected_address = utils.account_address_hex(parent_vasp.account_address)
    assert account.address == expected_address

    account = client.get_parent_vasp_account(parent_vasp.account_address)
    assert account.address == expected_address


def test_get_parent_vasp_account_not_found():
    client = testnet.create_client()
    parent_vasp = LocalAccount.generate()

    with pytest.raises(jsonrpc.AccountNotFoundError):
        client.get_parent_vasp_account(parent_vasp.account_address)


def test_get_parent_vasp_account_with_non_vasp_account_address():
    client = testnet.create_client()

    with pytest.raises(ValueError):
        client.get_parent_vasp_account(TREASURY_ADDRESS)


def test_gen_account():
    client = testnet.create_client()
    account = testnet.gen_account(client, base_url="http://hello.com")
    child_vasp = testnet.gen_child_vasp(client, account)

    assert client.get_account(account.account_address).role.type == "parent_vasp"
    assert client.get_account(child_vasp.account_address).role.type == "child_vasp"


def test_get_base_url_and_compliance_key():
    client = testnet.create_client()

    parent_vasp = testnet.gen_account(client, base_url="http://hello.com")
    child_vasp = testnet.gen_child_vasp(client, parent_vasp)

    base_url, key = client.get_base_url_and_compliance_key(child_vasp.account_address)
    assert base_url == "http://hello.com"
    assert utils.public_key_bytes(key) == parent_vasp.compliance_public_key_bytes
    base_url, key = client.get_base_url_and_compliance_key(parent_vasp.account_address)
    assert base_url == "http://hello.com"
    assert utils.public_key_bytes(key) == parent_vasp.compliance_public_key_bytes


def test_account_not_found_error_when_get_base_url_and_compliance_key_for_invalid_account():
    client = testnet.create_client()
    account = LocalAccount.generate()
    with pytest.raises(jsonrpc.AccountNotFoundError):
        client.get_base_url_and_compliance_key(account.account_address)


def test_value_error_when_get_base_url_and_compliance_key_for_account_has_no_base_url():
    client = testnet.create_client()
    with pytest.raises(ValueError):
        client.get_base_url_and_compliance_key(TREASURY_ADDRESS)


def test_gen_dd_account():
    client = testnet.create_client()
    account = testnet.gen_account(client, dd_account=True)
    onchain_account = client.get_account(account.account_address)
    assert onchain_account.role.type == "designated_dealer"


def test_init_faucet_with_url():
    client = testnet.create_client()
    faucet = testnet.Faucet(client, "invalid-url")
    with pytest.raises(ValueError):
        faucet.gen_account()


def test_get_vasp_domain_map():
    client = testnet.create_client()
    if not client.support_diem_id():
        pytest.skip("diem id not supported")
    faucet = testnet.Faucet(client)
    parent_vasp1 = faucet.gen_account()
    parent_vasp2 = faucet.gen_account()
    domain1 = "domain1"
    domain2 = "domain2"

    faucet.mint(parent_vasp1.auth_key.hex(), 1, testnet.TEST_CURRENCY_CODE, vasp_domain=domain1, is_remove_domain=False)
    faucet.mint(parent_vasp2.auth_key.hex(), 1, testnet.TEST_CURRENCY_CODE, vasp_domain=domain2, is_remove_domain=False)

    domain_map = client.get_vasp_domain_map()
    assert domain_map.get(domain1) == parent_vasp1.account_address.to_hex()
    assert domain_map.get(domain2) == parent_vasp2.account_address.to_hex()

    faucet.mint(parent_vasp1.auth_key.hex(), 1, testnet.TEST_CURRENCY_CODE, vasp_domain=domain1, is_remove_domain=True)
    domain_map = client.get_vasp_domain_map()
    assert domain_map.get(domain1) is None


def create_child_vasp_txn(
    parent_vasp: LocalAccount, child_vasp: LocalAccount, seq: int = 0
) -> diem_types.RawTransaction:
    script = stdlib.encode_create_child_vasp_account_script(
        coin_type=utils.currency_code(testnet.TEST_CURRENCY_CODE),
        child_address=child_vasp.account_address,
        auth_key_prefix=child_vasp.auth_key.prefix(),
        add_all_currencies=False,
        child_initial_balance=1_000_000,
    )

    return parent_vasp.sign(create_transaction(parent_vasp, script, seq))


def create_transaction(
    sender: LocalAccount, script: diem_types.Script, seq: int, currency=testnet.TEST_CURRENCY_CODE
) -> diem_types.RawTransaction:
    return diem_types.RawTransaction(
        sender=sender.account_address,
        sequence_number=seq,
        payload=diem_types.TransactionPayload__Script(script),
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code=currency,
        expiration_timestamp_secs=int(time.time()) + 30,
        chain_id=testnet.CHAIN_ID,
    )
