from unittest.mock import Mock, patch

import pylibra2._utils as utils
import pytest
from pylibra2 import LibraLedgerState


def ledger_state(chain_id, blockchain_version, blockchain_timestamp_usecs):
    return LibraLedgerState(
        chain_id=chain_id,
        blockchain_version=blockchain_version,
        blockchain_timestamp_usecs=blockchain_timestamp_usecs,
    )


@pytest.fixture
def test_keys_addr():
    return {
        "private_key": bytes.fromhex("82001573a003fd3b7fd72ffb0eaf63aac62f12deb629dca72785a66268ec758b"),
        "public_key": bytes.fromhex("664f6e8f36eacb1770fa879d86c2c1d0fafea145e84fa7d671ab7a011a54d509"),
        "auth_key": bytes.fromhex("231a656a51c1792efdb10f42ddbca0f80468de5bb622c235a681b898929cecf7"),
        "address": bytes.fromhex("0468de5bb622c235a681b898929cecf7"),
    }


def test_validate_ledger_state_success():
    utils.validate_ledger_state(
        ledger_state(chain_id=2, blockchain_version=100, blockchain_timestamp_usecs=1_000_0000),
        ledger_state(chain_id=2, blockchain_version=101, blockchain_timestamp_usecs=1_000_0001),
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
            ledger_state(chain_id=2, blockchain_version=99, blockchain_timestamp_usecs=1_000_0000),
            None,
            ValueError,
        ),
        # stale timestamp
        (
            ledger_state(chain_id=2, blockchain_version=100, blockchain_timestamp_usecs=999_9999),
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
def test_validate_ledger_state_fail(invalid_ledger_state, minimum_blockchain_timestamp_usecs, raised_exception):
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


@patch("cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey.generate")
def test_create_new_ed25519_key_pair(mock_private_key_generate, test_keys_addr):
    mock_private_key_generate.return_value = Mock(private_bytes=Mock(return_value=test_keys_addr["private_key"]))

    private_key, public_key = utils.LibraCryptoUtils.create_new_ed25519_key_pair()
    assert test_keys_addr["private_key"] == private_key
    assert test_keys_addr["public_key"] == public_key


def test_ed25519_public_key_from_private_key_success(test_keys_addr):
    public_key = utils.LibraCryptoUtils.ed25519_public_key_from_private_key(test_keys_addr["private_key"])

    assert test_keys_addr["public_key"] == public_key


def test_ed25519_public_key_from_private_key_fail(test_keys_addr):
    with pytest.raises(ValueError):
        utils.LibraCryptoUtils.ed25519_public_key_from_private_key(bytes.fromhex("ABCDEF"))


@patch("cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey.generate")
def test_create_account_success(mock_private_key_generate, test_keys_addr):
    mock_private_key_generate.return_value = Mock(private_bytes=Mock(return_value=test_keys_addr["private_key"]))
    account = utils.LibraCryptoUtils.LibraAccount.create()
    assert account.auth_key == test_keys_addr["auth_key"]
    assert account.address == test_keys_addr["address"]


def test_create_account_from_private_key_bytes_success(test_keys_addr):
    account = utils.LibraCryptoUtils.LibraAccount.create_from_private_key(test_keys_addr["private_key"])

    assert account.auth_key == test_keys_addr["auth_key"]
    assert account.address == test_keys_addr["address"]


def test_create_account_from_private_bytes_fail():
    with pytest.raises(ValueError):
        utils.LibraCryptoUtils.LibraAccount.create_from_private_key(bytes.fromhex("ABCDEF"))
