# pyre-strict

import pytest
import time
from pylibra import LibraNetwork, FaucetUtils, TransactionUtils, SubmitTransactionError, AccountKey, AccountResource


# TODO setup our own account with mint, so we can test non-zero cases
@pytest.mark.xfail
def test_account_state_block_from_testnet() -> None:
    # TODO: use another address generated in the genesis process.
    addr_hex = "00" * 32

    api = LibraNetwork()
    account = api.getAccount(addr_hex)
    # For all 0 address, these are the only attributes that will not change
    assert account.sequence == 0
    assert account.authentication_key == bytes.fromhex(addr_hex)
    assert not account.delegated_key_rotation_capability
    assert not account.delegated_withdrawal_capability
    # https://github.com/libra/libra/issues/2047
    # assert account.sent_events.count == 0


@pytest.mark.xfail
def test_non_existing_account() -> None:
    # just use an highly improbable address for now
    addr_hex = "ff" * 32
    addr_bytes = bytes.fromhex(addr_hex)

    api = LibraNetwork()
    account = api.getAccount(addr_hex)
    assert account.address == addr_bytes
    assert account.authentication_key == addr_bytes
    assert account.balance == 0
    assert account.sequence == 0


@pytest.mark.xfail
def test_send_transaction_fail() -> None:
    RECEIVER_ADDRESS = bytes.fromhex("00" * 32)
    PRIVATE_KEY = bytes.fromhex("ff" * 32)

    api = LibraNetwork()

    tx = TransactionUtils.createSignedP2PTransaction(
        PRIVATE_KEY,
        RECEIVER_ADDRESS,
        # sequence
        255,
        # 1 libra
        1_000_000,
        expiration_time=0,
    )

    with pytest.raises(SubmitTransactionError) as excinfo:
        api.sendTransaction(tx.byte)
    assert (
        # not enough money
        excinfo.value.message == "VM Status, major code 7, sub code 0, message: 'sender address: "
        "45aacd9ed90a5a8e211502ac3fa898a3819f23b2e4c98dfff47e76274a708451'."
    )


@pytest.mark.xfail
def test_mint() -> None:
    RECEIVER_ADDRESS = "11" * 32

    f = FaucetUtils()
    seq = f.mint(RECEIVER_ADDRESS, 1.5)

    assert 0 != seq


def _wait_for_account_seq(addr_hex: str, seq: int) -> AccountResource:
    api = LibraNetwork()
    while True:
        ar = api.getAccount(addr_hex)
        if ar.sequence >= seq:
            return ar
        time.sleep(0.1)


@pytest.mark.timeout(10)
@pytest.mark.xfail
def test_send_transaction_success() -> None:
    assoc_address = "000000000000000000000000000000000000000000000000000000000a550c18"

    private_key = bytes.fromhex("82001573a003fd3b7fd72ffb0eaf63aac62f12deb629dca72785a66268ec758b")
    addr_bytes = AccountKey(private_key).address
    addr_hex = bytes.hex(addr_bytes)

    api = LibraNetwork()

    f = FaucetUtils()
    seq = f.mint(addr_hex, 1)
    _ = _wait_for_account_seq(assoc_address, seq)

    ar = api.getAccount(addr_hex)
    balance = ar.balance
    seq = ar.sequence

    tx = TransactionUtils.createSignedP2PTransaction(
        private_key,
        bytes.fromhex(assoc_address),
        # sequence
        seq,
        # 1 libra
        1_000_000,
        expiration_time=int(time.time()) + 5 * 60,
    )
    api.sendTransaction(tx.byte)
    ar = _wait_for_account_seq(addr_hex, seq + 1)

    assert ar.sequence == seq + 1
    assert ar.balance == balance - 1_000_000


@pytest.mark.xfail
def test_transaction_by_range() -> None:
    api = LibraNetwork()
    txs = api.transactions_by_range(0, 1)
    # genesis txns are WriteSet, and we don't support it, so we always get an empty list back.
    assert txs == []


@pytest.mark.xfail
def test_transaction_by_acc_seq() -> None:
    assoc_address = "000000000000000000000000000000000000000000000000000000000a550c18"

    api = LibraNetwork()
    tx = api.transaction_by_acc_seq(assoc_address, 1)
    # mint transaction are not yet supported
    assert tx is None
