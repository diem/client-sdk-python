import calibra.lib.clients.pylibra2._utils as utils
import pytest
from calibra.lib.clients.pylibra2 import LibraLedgerState


def ledger_state(chain_id, blockchain_version, blockchain_timestamp_usecs):
    return LibraLedgerState(
        chain_id=chain_id,
        blockchain_version=blockchain_version,
        blockchain_timestamp_usecs=blockchain_timestamp_usecs,
    )


def test_validate_ledger_state_success():
    utils.validate_ledger_state(
        ledger_state(
            chain_id=2, blockchain_version=100, blockchain_timestamp_usecs=1_000_0000
        ),
        ledger_state(
            chain_id=2, blockchain_version=101, blockchain_timestamp_usecs=1_000_0001
        ),
    )


@pytest.mark.parametrize(
    "invalid_ledger_state, minimum_blockchain_timestamp_usecs, raised_exception",
    [
        # not matching chain_id
        (
            ledger_state(
                chain_id=3,
                blockchain_version=100,
                blockchain_timestamp_usecs=1_000_0000,
            ),
            None,
            ValueError,
        ),
        # stale version
        (
            ledger_state(
                chain_id=2, blockchain_version=99, blockchain_timestamp_usecs=1_000_0000
            ),
            None,
            ValueError,
        ),
        # stale timestamp
        (
            ledger_state(
                chain_id=2, blockchain_version=100, blockchain_timestamp_usecs=999_9999
            ),
            None,
            ValueError,
        ),
        # minimum_blockchain_timestamp_usecs higher than received
        (
            ledger_state(
                chain_id=2,
                blockchain_version=100,
                blockchain_timestamp_usecs=1_000_0000,
            ),
            1_000_0001,
            ValueError,
        ),
    ],
)
def test_validate_ledger_state_fail(
    invalid_ledger_state, minimum_blockchain_timestamp_usecs, raised_exception
):
    with pytest.raises(raised_exception):
        utils.validate_ledger_state(
            ledger_state(
                chain_id=2,
                blockchain_version=100,
                blockchain_timestamp_usecs=1_000_0000,
            ),
            invalid_ledger_state,
            minimum_blockchain_timestamp_usecs,
        )
