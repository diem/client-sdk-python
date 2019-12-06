from pylibra import LibraNetwork


# TODO setup our own account with mint, so we can test non-zero cases
def test_account_state_block_from_testnet():
    # TODO: use another address generated in the genesis process.
    addr_hex = "00" * 32

    api = LibraNetwork()
    account = api.getAccount(addr_hex)
    # For all 0 address, these are the only attributes that will not change
    assert account.sequence == 0
    assert account.authentication_key == bytes.fromhex(addr_hex)
    assert not account.delegated_key_rotation_capability
    assert not account.delegated_withdrawal_capability
    assert account.sent_events.count == 0
