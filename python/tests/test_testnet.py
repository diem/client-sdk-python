# pyre-strict

import pytest
import time
from pylibra import (
    LibraNetwork,
    FaucetUtils,
    TransactionUtils,
    SubmitTransactionError,
    AccountKey,
    AccountResource,
    FaucetError,
    PaymentEvent,
)
from functools import wraps
import typing

ASSOC_ADDRESS: str = "000000000000000000000000000000000000000000000000000000000a550c18"

RT = typing.TypeVar("RT")
TFun = typing.Callable[..., typing.Optional[RT]]


def retry(
    exceptions: typing.Type[Exception],
    tries: int = 4,
    delay: int = 3,
    backoff: int = 2,
    logger: typing.Optional[typing.Callable[[str], None]] = None,
) -> typing.Callable[[TFun], TFun]:
    """
    Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions: The exception to check. may be a tuple of
            exceptions to check.
        tries: Number of times to try (not retry) before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier (e.g. value of 2 will double the delay
            each retry).
        logger: Logger to use. If None, print.
    """

    def deco_retry(f: TFun) -> TFun:
        @wraps(f)
        def f_retry(*args, **kwargs):  # pyre-ignore
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = "{}, Retrying in {} seconds...".format(e, mdelay)
                    if logger:
                        logger(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return typing.cast(TFun, f_retry)  # true decorator

    return deco_retry


# TODO setup our own account with mint, so we can test non-zero cases
@pytest.mark.xfail
def test_account_state_block_from_testnet() -> None:
    # TODO: use another address generated in the genesis process.
    api = LibraNetwork()
    account = api.getAccount(ASSOC_ADDRESS)
    # For assoc address, we can only know a few things
    assert account is not None
    assert account.sequence > 0
    assert account.balance > 0
    assert account.authentication_key != bytes.fromhex(ASSOC_ADDRESS)
    assert not account.delegated_key_rotation_capability
    assert not account.delegated_withdrawal_capability


@pytest.mark.xfail
def test_non_existing_account() -> None:
    # just use an highly improbable address for now
    addr_hex = "ff" * 32

    api = LibraNetwork()
    account = api.getAccount(addr_hex)
    assert account is None


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


@pytest.mark.timeout(30)
@pytest.mark.xfail
def test_mint() -> None:
    RECEIVER_ADDRESS: str = "11" * 32

    @retry(FaucetError, delay=1)
    def _mint() -> None:
        f = FaucetUtils()
        seq = f.mint(RECEIVER_ADDRESS, 1.5)
        assert 0 != seq

    _mint()


def _wait_for_account_seq(addr_hex: str, seq: int) -> AccountResource:
    api = LibraNetwork()
    while True:
        ar = api.getAccount(addr_hex)
        if ar is not None and ar.sequence >= seq:
            return ar
        time.sleep(1)


@pytest.mark.timeout(60)
@pytest.mark.xfail
def test_send_transaction_success() -> None:
    private_key = bytes.fromhex("82001573a003fd3b7fd72ffb0eaf63aac62f12deb629dca72785a66268ec758b")
    addr_bytes = AccountKey(private_key).address
    addr_hex: str = bytes.hex(addr_bytes)

    api = LibraNetwork()

    @retry(FaucetError, delay=1)
    def _mint_and_wait(amount: int) -> AccountResource:
        f = FaucetUtils()
        seq = f.mint(addr_hex, amount)
        return _wait_for_account_seq(ASSOC_ADDRESS, seq)

    _mint_and_wait(1)

    ar = api.getAccount(addr_hex)

    assert ar is not None
    balance = ar.balance
    seq = ar.sequence

    tx = TransactionUtils.createSignedP2PTransaction(
        private_key,
        bytes.fromhex(ASSOC_ADDRESS),
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
    res = api.transactions_by_range(0, 10)
    assert len(res) == 10
    tx, _ = res[0]
    assert tx.sender == bytes.fromhex(ASSOC_ADDRESS)
    assert tx.version == 0


@pytest.mark.xfail
def test_transaction_by_range_with_events() -> None:
    api = LibraNetwork()
    res = api.transactions_by_range(0, 10, True)
    assert len(res) == 10
    tx, events = res[0]
    assert tx.sender == bytes.fromhex(ASSOC_ADDRESS)
    assert tx.version == 0
    assert len(events) == 4
    assert events[0].module == "LibraAccount"

    assert type(events[0]) == PaymentEvent
    e = typing.cast(PaymentEvent, events[0])
    assert e.is_sent is True

    assert type(events[1]) == PaymentEvent
    e = typing.cast(PaymentEvent, events[1])
    assert e.module == "LibraAccount"
    assert e.is_received is True

    assert events[2].module == "LibraSystem"
    assert events[2].name == "ValidatorSetChangeEvent"
    assert events[3].module == "LibraSystem"
    assert events[3].name == "DiscoverySetChangeEvent"


@pytest.mark.xfail
def test_transaction_by_acc_seq() -> None:
    api = LibraNetwork()
    tx, _ = api.transaction_by_acc_seq(ASSOC_ADDRESS, 1, include_events=True)
    assert tx
    assert tx.sender == bytes.fromhex(ASSOC_ADDRESS)
    assert tx.version != 0
    assert tx.gas == 0


@pytest.mark.xfail
def test_transaction_by_acc_seq_with_events() -> None:
    api = LibraNetwork()
    tx, events = api.transaction_by_acc_seq(ASSOC_ADDRESS, 1, include_events=True)
    assert tx
    assert tx.sender == bytes.fromhex(ASSOC_ADDRESS)
    assert tx.version != 0
    assert len(events) == 2
    assert events[0].module == "LibraAccount"
    assert tx.gas == 0


@pytest.mark.xfail
def test_timestamp_from_testnet() -> None:
    api = LibraNetwork()
    assert api.currentTimestampUsecs() > 0


@pytest.mark.xfail
def test_mint_sum() -> None:
    api = LibraNetwork()

    account = api.getAccount(ASSOC_ADDRESS)
    assert account is not None

    print("Account Balance:", account.balance, "Sequence:", account.sequence)
    total = 0
    seq = 0
    while seq < min(account.sequence, 10):
        tx, events = api.transaction_by_acc_seq(ASSOC_ADDRESS, seq=seq, include_events=True)
        if tx and tx.is_mint:
            print("Found mint transaction: from: ", tx.sender.hex())
            total = total + tx.amount
            print("New Total:", total)
        seq = seq + 1
    assert total > 0
