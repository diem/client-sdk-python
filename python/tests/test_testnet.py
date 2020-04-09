# pyre-strict

import pytest
import time
from pylibra import (
    LibraNetwork,
    FaucetUtils,
    AccountKeyUtils,
    TransactionUtils,
    SubmitTransactionError,
    AccountResource,
    FaucetError,
    PaymentEvent,
)
from functools import wraps
import typing

ASSOC_ADDRESS: str = "0000000000000000000000000a550c18"
ASSOC_AUTHKEY: str = "3126dc954143b1282565e8829cd8cdfdc179db444f64b406dee28015fce7f392"

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


# Assoc address is generated in the genesis process.
def test_assoc_account() -> None:
    api = LibraNetwork()
    account = api.getAccount(ASSOC_ADDRESS)
    # For assoc address, we can only know a few things
    assert account is not None
    assert account.sequence > 0
    assert account.balance > 0
    assert account.authentication_key.hex() == ASSOC_AUTHKEY
    assert not account.delegated_key_rotation_capability
    assert not account.delegated_withdrawal_capability


def test_non_existing_account() -> None:
    # just use an highly improbable address for now
    addr_hex = "ff" * 16

    api = LibraNetwork()
    account = api.getAccount(addr_hex)
    assert account is None


def test_send_transaction_fail() -> None:
    RECEIVER_ADDRESS = bytes.fromhex("01" * 16)
    RECEIVER_AUTHKEY_PREFIX = bytes.fromhex("01" * 16)

    PRIVATE_KEY = bytes.fromhex("deadbeef" * 8)

    api = LibraNetwork()

    tx = TransactionUtils.createSignedP2PTransaction(
        PRIVATE_KEY,
        RECEIVER_ADDRESS,
        RECEIVER_AUTHKEY_PREFIX,
        # sequence
        255,
        # 1 libra
        1_000_000,
        expiration_time=int(time.time()) + 5 * 60,
    )

    print("Submitting: " + tx.hex())

    with pytest.raises(SubmitTransactionError) as excinfo:
        api.sendTransaction(tx)
    # vm validation error
    assert excinfo.value.code == -32001
    # account doesn't exists
    assert excinfo.value.data["major_status"] == 7


@pytest.mark.timeout(30)
def test_mint() -> None:
    RECEIVER_AUTHKEY_HEX: str = "11" * 32

    @retry(FaucetError, delay=1)
    def _mint() -> None:
        f = FaucetUtils()
        seq = f.mint(RECEIVER_AUTHKEY_HEX, 1.5)
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
def test_send_transaction_success() -> None:
    private_key = bytes.fromhex("82001573a003fd3b7fd72ffb0eaf63aac62f12deb629dca72785a66268ec758b")

    ak = AccountKeyUtils.from_private_key(private_key)
    authkey_hex: str = ak.authentication_key.hex()
    addr_hex = ak.address.hex()
    api = LibraNetwork()

    @retry(FaucetError, delay=1)
    def _mint_and_wait(amount: int) -> AccountResource:
        f = FaucetUtils()
        seq = f.mint(authkey_hex, amount)
        return _wait_for_account_seq(ASSOC_ADDRESS, seq)

    _mint_and_wait(1)

    ar = api.getAccount(addr_hex)
    assert ar is not None
    balance = ar.balance
    seq = ar.sequence

    tx = TransactionUtils.createSignedP2PTransaction(
        private_key,
        bytes.fromhex(ASSOC_ADDRESS),
        bytes.fromhex(ASSOC_AUTHKEY[: len(ASSOC_ADDRESS)]),
        # sequence
        seq,
        # 1 libra
        1_000_000,
        expiration_time=int(time.time()) + 5 * 60,
    )
    api.sendTransaction(tx)
    ar = _wait_for_account_seq(addr_hex, seq + 1)

    assert ar.sequence == seq + 1
    assert ar.balance == balance - 1_000_000


def test_transaction_by_range() -> None:
    api = LibraNetwork()
    res = api.transactions_by_range(0, 10)
    assert len(res) == 10
    # todo: verify the first txn is an WriteSet


def test_transaction_by_range_with_events() -> None:
    api = LibraNetwork()
    res = api.transactions_by_range(0, 10, True)
    assert len(res) == 10
    _, events = res[0]
    assert len(events) == 4
    assert events[0].module == "LibraAccount"

    assert isinstance(events[0], PaymentEvent)
    e = typing.cast(PaymentEvent, events[0])
    assert e.is_sent is True

    assert isinstance(events[1], PaymentEvent)
    e = typing.cast(PaymentEvent, events[1])
    assert e.module == "LibraAccount"
    assert e.is_received is True

    assert events[2].module == "Unknown"
    assert events[2].name == "Unknown"
    assert events[3].module == "Unknown"
    assert events[3].name == "Unknown"


def test_transaction_by_acc_seq_not_exist() -> None:
    api = LibraNetwork()
    tx, events = api.transaction_by_acc_seq("00000000000000000000000000000000", 0, include_events=True)
    assert tx is None
    assert events == []


def test_transaction_by_acc_seq() -> None:
    api = LibraNetwork()
    tx, _ = api.transaction_by_acc_seq(ASSOC_ADDRESS, 1, include_events=True)
    assert tx
    assert tx.sender == bytes.fromhex(ASSOC_ADDRESS)
    assert tx.version != 0
    assert tx.gas == 0


def test_transaction_by_acc_seq_with_events() -> None:
    api = LibraNetwork()
    tx, events = api.transaction_by_acc_seq(ASSOC_ADDRESS, 1, include_events=True)
    assert tx
    assert tx.sender == bytes.fromhex(ASSOC_ADDRESS)
    assert tx.version != 0
    assert len(events) == 2
    assert events[0].module == "LibraAccount"
    assert tx.gas == 0


def test_timestamp_from_testnet() -> None:
    api = LibraNetwork()
    assert api.currentTimestampUsecs() > 0


def test_version_from_testnet() -> None:
    api = LibraNetwork()
    assert api.currentVersion() > 1


def test_assoc_events() -> None:
    api = LibraNetwork()
    ar = api.getAccount(ASSOC_ADDRESS)
    assert ar is not None
    events = api.get_events(ar.sent_events_key.hex(), 0, 1)
    assert len(events) == 1


def test_no_events() -> None:
    api = LibraNetwork()
    events = api.get_events("00" * 8 + "00" * 16, 0, 1)
    assert len(events) == 0


def test_assoc_mint_sum() -> None:
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
