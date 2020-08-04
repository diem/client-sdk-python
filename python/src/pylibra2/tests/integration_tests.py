import random
import time

from calibra.lib.clients.pylibra2 import (
    ASSOC_ADDRESS,
    ASSOC_AUTHKEY,
    AccountKeyUtils,
    ClientError,
    LibraClient,
    SubmitTransactionError,
    TransactionUtils,
)


# [TODO] Can write a decorator?? Less overhead than a function!
def add_separator(end: bool = False):
    print("=" * 64)
    if end:
        print("\n")


def get_test_account():
    # generate random address every time
    random_str = str(random.randrange(100_000_00, 100_000_000)) * 8
    private_key = bytes.fromhex(random_str)

    account_ak = AccountKeyUtils.from_private_key(private_key)

    return account_ak


def get_p2p_signed_transaction_bytes(
    sender_private_key: bytes, receiver_address: bytes, sender_sequence: int
):
    signed_tx_bytes = TransactionUtils.createSignedP2PTransaction(
        sender_private_key,
        receiver_address,
        # sequence
        sender_sequence,
        # micro libra
        1_000_000,
        expiration_time=int(time.time()) + 5 * 60,
    )

    return signed_tx_bytes


def test_mint_and_wait():
    add_separator()

    print("Testing mint_and_wait func....")

    is_failed = False
    account = get_test_account()
    libra_client = LibraClient()

    try:
        libra_client.mint_and_wait(account.authentication_key.hex(), 1_000_000, "LBR")
    except ClientError as e:
        print("Integration test of `mint_and_wait` failed. Please check!!")
        print(str(e))
        is_failed = True

    # [TODO] Write a macro? Can we do it for python?
    if not is_failed:
        print("Integration test of `mint_and_wait` success!")

    add_separator(end=True)


def test_submit_and_wait():
    add_separator()

    print("Testing submit_and_wait func....")

    is_failed = False
    libra_client = LibraClient()

    account1 = get_test_account()
    account2 = get_test_account()

    # minting money to both accounts
    # [TODO] retry if it fails -> use the decorator in Pylibra tests
    libra_client.mint_and_wait(account1.authentication_key.hex(), 1_000_000, "LBR")
    libra_client.mint_and_wait(account2.authentication_key.hex(), 1_000_000, "LBR")

    # [TODO] sequence number for account should be extracted using account resource & then use
    signed_tx_bytes = get_p2p_signed_transaction_bytes(
        account1.private_key, account2.address, sender_sequence=0
    )

    try:
        libra_client.submit_and_wait(signed_tx_bytes)
    except (SubmitTransactionError, ClientError) as e:
        print("Integration test of `submit_and_wait` failed. Please check!!")
        print(str(e))
        is_failed = True

    if not is_failed:
        print("Integration test of `submit_and_wait` success!")

    add_separator(end=True)


def test_get_account_exists():
    add_separator()

    print("Testing get_account func for an existing account...")

    is_failed = False
    libra_client = LibraClient()

    try:
        association_account = libra_client.get_account(ASSOC_ADDRESS)
    except ClientError as e:
        print(
            "Integration test of `get_account` failed for an existing account. Please check!!"
        )
        print(f"Error: {e}")
        is_failed = True

    assert association_account is not None
    assert association_account.sequence > 0
    assert association_account.authentication_key == ASSOC_AUTHKEY
    assert not association_account.delegated_key_rotation_capability
    assert not association_account.delegated_withdrawal_capability

    if not is_failed:
        print("Integration test of `get_account` success for an existing account!")

    add_separator(end=True)


def test_p2p_transaction():
    add_separator()

    print("Testing transfer_coin_peer_to_peer func....")

    is_failed = False

    # two accounts
    account1 = get_test_account()
    account2 = get_test_account()

    client = LibraClient()

    # minting money to account1
    client.mint_and_wait(account1.authentication_key.hex(), 1_00_000)

    # minting money to account2
    client.mint_and_wait(account2.authentication_key.hex(), 1_00_000)

    # getting account states
    account1_state = client.get_account(account1.address.hex())
    account2_state = client.get_account(account2.address.hex())

    # sanity checking them
    assert account1_state is not None
    assert account1_state.balances["LBR"] >= 1_00_000
    account1_balance_before_transfer = account1_state.balances["LBR"]

    assert account2_state is not None
    assert account2_state.balances["LBR"] >= 1_00_000
    account2_balance_before_transfer = account2_state.balances["LBR"]

    # create trasaction
    client.transfer_coin_peer_to_peer(
        account1.private_key.hex(),
        account2.address.hex(),
        account1_state.sequence,
        1_00_000,
        expiration_timestamp=int(time.time()) + 5 * 60,
    )

    # TODO (ssinghaldev) once the events are implemented, check that.
    # It is more robust than balances as there could be some other tx in between although its unlikely

    # check the balances again
    account1_state = client.get_account(account1.address.hex())
    account2_state = client.get_account(account2.address.hex())

    account1_balance_after_transfer = account1_state.balances["LBR"]
    account2_balance_after_transfer = account2_state.balances["LBR"]

    assert account1_balance_after_transfer == (
        account1_balance_before_transfer - 1_00_000
    )
    assert account2_balance_after_transfer == (
        account2_balance_before_transfer + 1_00_000
    )

    if not is_failed:
        print(
            "Integration test of `transfer_coin_peer_to_peer` success for an existing account!"
        )

    add_separator(end=True)


if __name__ == "__main__":
    # mint_and_wait integeration test
    test_mint_and_wait()

    # submit_and_wait integeration test
    test_submit_and_wait()

    # get_account_state integeration test
    test_get_account_exists()

    # test peer to peer transaction
    test_p2p_transaction()
