from pylibra import LibraNetwork, FaucetUtils, TransactionUtils, SubmitTransactionError


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


def test_send_trasncation():
    RECEIVER_ADDRESS = bytes.fromhex("00" * 32)
    PRIVATE_KEY = bytes.fromhex("22" * 32)

    api = LibraNetwork()

    tx = TransactionUtils.createSignedP2PTransaction(
        PRIVATE_KEY,
        RECEIVER_ADDRESS,
        # sequence
        255,
        # 1 libra
        1_000_000,
    )

    try:
        api.sendTransaction(tx.bytes)
    except SubmitTransactionError as e:
        assert (
            e.message == "VM Status, major code 7, sub code 0, message: 'sender address: "
            "0fce042fb21f424ee71e2a1b00a07f55b3421a3a4d6de31aafe5cc740fd64922'."
        )


def test_mint():
    RECEIVER_ADDRESS = bytes.fromhex("00" * 32)

    f = FaucetUtils()
    seq = f.mint(RECEIVER_ADDRESS, 1.5)

    assert 0 == seq
