import time

from pylibra2 import (
    ASSOC_ADDRESS,
    ChainId,
    ClientError,
    LibraClient,
    LibraCryptoUtils,
    SubmitTransactionError,
    TxStatus,
    stdlib,
    _utils,
    libra_types as libra,
    lcs,
    serde_types as st,
)
from pylibra2._config import CORE_CODE_ADDRESS


# [TODO] Can write a decorator?? Less overhead than a function!
def add_separator(end: bool = False):
    print("=" * 64)
    if end:
        print("\n")


def get_test_account() -> LibraCryptoUtils.LibraAccount:
    return LibraCryptoUtils.LibraAccount.create()


def get_p2p_signed_transaction_bytes(sender_private_key: bytes, receiver_address: bytes, sender_sequence: int):
    lbr_type_tag = libra.TypeTag__Struct(
        value=libra.StructTag(
            address=_utils.make_libra_account_address(CORE_CODE_ADDRESS),
            module=libra.Identifier("LBR"),
            name=libra.Identifier("LBR"),
            type_params=[],
        )
    )
    tx_script: libra.Script = stdlib.encode_peer_to_peer_with_metadata_script(
        currency=lbr_type_tag,
        payee=_utils.make_libra_account_address(receiver_address.hex()),
        amount=st.uint64(1_000_000),
        metadata=b"",
        metadata_signature=b"",
    )

    account = LibraCryptoUtils.LibraAccount.create_from_private_key(sender_private_key)
    raw_txn = libra.RawTransaction(
        _utils.make_libra_account_address(account.address.hex()),
        st.uint64(sender_sequence),
        libra.TransactionPayload__Script(value=tx_script),
        st.uint64(1_000_000),
        st.uint64(0),
        "LBR",
        st.uint64(time.time() + 5 * 60),
        libra.ChainId(value=st.uint8(ChainId.TESTNET)),
    )
    # LCS of the Raw Transaction
    raw_tx_bytes: bytes = lcs.serialize(raw_txn, libra.RawTransaction)

    # Adding seed to LCS bytes
    raw_tx_bytes_hash = LibraCryptoUtils.add_seed_to_raw_tx_bytes(raw_tx_bytes)

    # Signing the resulting bytes
    signature = LibraCryptoUtils.ed25519_sign(sender_private_key, raw_tx_bytes_hash)

    # Assembling them in the Struct
    public_key_bytes = LibraCryptoUtils.ed25519_public_key_from_private_key(sender_private_key)
    signed_tx = libra.SignedTransaction(
        raw_txn=raw_txn,
        authenticator=libra.TransactionAuthenticator__Ed25519(
            public_key=libra.Ed25519PublicKey(public_key_bytes),
            signature=libra.Ed25519Signature(value=signature),
        ),
    )
    signed_tx_bytes = lcs.serialize(signed_tx, libra.SignedTransaction)
    return signed_tx_bytes


def test_mint_and_wait():
    add_separator()

    print("Testing mint_and_wait func....")

    is_failed = False
    account = get_test_account()
    libra_client = LibraClient()

    try:
        libra_client.mint_and_wait(account.auth_key.hex(), 1_000_000, "LBR")
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
    libra_client.mint_and_wait(account1.auth_key.hex(), 1_000_000, "LBR")
    libra_client.mint_and_wait(account2.auth_key.hex(), 1_000_000, "LBR")

    # [TODO] sequence number for account should be extracted using account resource & then use
    signed_tx_bytes = get_p2p_signed_transaction_bytes(account1.private_key, account2.address, sender_sequence=0)

    try:
        tx_status = libra_client.submit_transaction_and_wait(signed_tx_bytes)
    except SubmitTransactionError as e:
        print("Integration test of `submit_and_wait` failed. Please check!!")
        print(str(e))
        is_failed = True

    if tx_status != TxStatus.SUCCESS:
        print("Integration test of `submit_and_wait` failed. Please check!!")
        print(f"TxStatus: {tx_status}")
        is_failed = True

    if not is_failed:
        print("Integration test of `submit_and_wait` success!")

    add_separator(end=True)


def test_get_currencies():
    add_separator()

    print("Testing get_currencies func...")
    is_failed = False
    libra_client = LibraClient()

    try:
        res = libra_client.get_currencies()
    except ClientError as e:
        print("Integration test of `get_currencies` failed. Please check!!")
        print(f"Error: {e}")
        is_failed = True

    assert res is not None
    assert len(res) > 0

    if not is_failed:
        print("Integration test of `get_currencies` successed!")

    add_separator(end=True)


def test_get_account_exists():
    add_separator()

    print("Testing get_account func for an existing account...")

    is_failed = False
    libra_client = LibraClient()

    try:
        association_account = libra_client.get_account(ASSOC_ADDRESS)
    except ClientError as e:
        print("Integration test of `get_account` failed for an existing account. Please check!!")
        print(f"Error: {e}")
        is_failed = True

    assert association_account is not None
    assert association_account.sequence > 0
    assert association_account.authentication_key is not None
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
    client.mint_and_wait(account1.auth_key.hex(), 1_00_000)

    # minting money to account2
    client.mint_and_wait(account2.auth_key.hex(), 1_00_000)

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
        sender_private_key=account1.private_key.hex(),
        sender_sequence=account1_state.sequence,
        currency_identifier="LBR",
        receiver=account2.address.hex(),
        amount=1_00_000,
        expiration_timestamp_secs=int(time.time()) + 5 * 60,
    )

    # TODO (ssinghaldev) once the events are implemented, check that.
    # It is more robust than balances as there could be some other tx in between although its unlikely

    # check the balances again
    account1_state = client.get_account(account1.address.hex())
    account2_state = client.get_account(account2.address.hex())

    account1_balance_after_transfer = account1_state.balances["LBR"]
    account2_balance_after_transfer = account2_state.balances["LBR"]

    assert account1_balance_after_transfer == (account1_balance_before_transfer - 1_00_000)
    assert account2_balance_after_transfer == (account2_balance_before_transfer + 1_00_000)

    if not is_failed:
        print("Integration test of `transfer_coin_peer_to_peer` success for an existing account!")

    add_separator(end=True)
