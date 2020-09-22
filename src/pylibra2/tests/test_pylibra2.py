import time
import typing
from unittest.mock import MagicMock, call, patch

import pytest
from calibra.lib.clients.pylibra2 import (
    DEFAULT_JSON_RPC_SERVER,
    ChainId,
    ClientError,
    LibraAccount,
    LibraBlockMetadataTransaction,
    LibraClient,
    LibraCryptoUtils,
    LibraP2PScript,
    LibraPaymentEvent,
    LibraUnknownTransaction,
    LibraUserTransaction,
    LibraWriteSetTransaction,
    SubmitTransactionError,
    TransactionUtils,
    TxStatus,
    lcs,
    libra_types as libra,
)
from calibra.lib.clients.pylibra2._config import (
    DEFAULT_CONNECT_TIMEOUT_SECS,
    DEFAULT_LIBRA_CHAIN_ID,
    DEFAULT_TIMEOUT_SECS,
    JSONRPC_LIBRA_CHAIN_ID,
    JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS,
    JSONRPC_LIBRA_LEDGER_VERSION,
    MAX_WAIT_ITERATIONS,
)
from requests.exceptions import RequestException


MOCK_SUCCESSFUL_SUBMIT_RESPONSE: typing.Dict[str, typing.Any] = {
    "id": 1,
    "jsonrpc": "2.0",
    JSONRPC_LIBRA_CHAIN_ID: 2,
    JSONRPC_LIBRA_LEDGER_VERSION: 1000,
    JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
    "result": None,
}


def get_mock_transaction(
    tx_type: str = "user", script_type: str = "p2p", with_events: bool = False
):
    mock_tx = {
        "transaction": {
            "expiration_timestamp_secs": 1590680747,
            "gas_unit_price": 0,
            "gas_currency": "LBR",
            "max_gas_amount": 1000000,
            "public_key": "500a9002995e1af93bbdaf977385ed507b174bb3dc6936efd72612d56198a19d",
            "script": {
                "amount": 10000000,
                "currency": "LBR",
                "metadata": "",
                "metadata_signature": "",
                "receiver": "4ac94d88e90acd4cf0294e898e421e94",
                "type": "peer_to_peer_transaction",
            },
            "script_hash": "c8bc3dda60e9662965b3223c22e3d3e3e7b6f698cf1a6930a449eb99daa35e7c",
            "script_bytes": "",
            "sender": "c1fda0ec67c1b87bfb9e883e2080e530",
            "sequence_number": 0,
            "signature": "fe335285e5d87db25f86041d033414bfdf77ddae6f0dfbdc65ff4f5965ff810ef9c85ce00ede0820ce0cf5903f9ab3e93fa6e49bbf770aba9b083a985361fa01",
            "signature_scheme": "Scheme::Ed25519",
            "type": "user",
            "chain_id": 2,
        },
        "events": [],
        "version": 4433485,
        "vm_status": "executed",
        "gas_used": 0,
        "hash": "500a9002995e1af93bbdaf977385ed507b174bb3dc6936efd72612d56198a19f",
        "bytes": "",
    }

    if tx_type != "user":
        tx_dict = {}
        if tx_type == "blockmetadata":
            tx_dict = {
                "transaction": {
                    "type": "blockmetadata",
                    "timestamp_usecs": 1594157471000000,
                }
            }
        elif tx_type == "writeset":
            tx_dict = {"transaction": {"type": "writeset"}}
        elif tx_type == "unknown":
            tx_dict = {"transaction": {"type": "unknown"}}

        mock_tx["transaction"] = tx_dict["transaction"]  # pyre-ignore

    if tx_type == "user":
        if script_type != "p2p":
            script_dict = {}
            if script_type == "mint":
                script_dict = {
                    "script": {
                        "amount": 10000000,
                        "currency": "LBR",
                        "receiver": "4ac94d88e90acd4cf0294e898e421e94",
                        "type": "mint",
                    }
                }
            elif script_type == "unknown":
                script_dict = {"script": {"type": "unknown"}}

            mock_tx["transaction"]["script"] = script_dict["script"]  # pyre-ignore

    if with_events:
        event_dict = {
            "events": [
                {
                    "key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e530",
                    "sequence_number": 0,
                    "transaction_version": 4433485,
                    "data": {
                        "amount": {"amount": 10000000, "currency": "LBR"},
                        "metadata": "",
                        "sender": "4ac94d88e90acd4cf0294e898e421e94",
                        "receiver": "4ac94d88e90acd4cf0294e898e421e94",
                        "type": "sentpayment",
                    },
                }
            ]
        }

        mock_tx["events"] = event_dict["events"]

    return mock_tx


def get_mock_event(event_type: str = "sent"):
    mock_event = {
        "key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e530",
        "sequence_number": 0,
        "transaction_version": 4433485,
        "data": {
            "amount": {"amount": 10000000, "currency": "LBR"},
            "metadata": "",
            "sender": "4ac94d88e90acd4cf0294e898e421e94",
            "receiver": "4ac94d88e90acd4cf0294e898e421e94",
            "type": "sentpayment",
        },
    }

    if event_type != "sent":
        event_data_dict = {}

        if event_type == "received":
            event_data_dict = {
                "data": {
                    "amount": {"amount": 10000000, "currency": "LBR"},
                    "metadata": "",
                    "sender": "4ac94d88e90acd4cf0294e898e421e94",
                    "receiver": "4ac94d88e90acd4cf0294e898e421e94",
                    "type": "receivedpayment",
                }
            }
        elif event_type == "unknown":
            event_data_dict = {"data": {"type": "unknown"}}

        mock_event["data"] = event_data_dict["data"]

    return mock_event


def get_side_effect_for_wait_failures(which_func: str) -> typing.List[typing.Any]:
    side_effect = []
    if which_func == "mint":
        side_effect.append(MagicMock(text=0, ok=True))
    elif which_func == "submit":
        side_effect.append(
            MagicMock(json=MagicMock(return_value=MOCK_SUCCESSFUL_SUBMIT_RESPONSE))
        )

    # Have to generate RequestException MAX_WAIT_ITERATIONS bcoz if there is network error,
    # the wait function will retry till it times out
    for _ in range(MAX_WAIT_ITERATIONS):
        side_effect.append(RequestException)

    return side_effect


def get_valid_tx_response(
    signed_tx_bytes: bytes, tx_resp: typing.Dict[str, typing.Any]
):
    """ Function to generate correct tx_response (appropriate signature/public key/sender/receiver/amount) depending on signed tx bytes

        This func is needed for checking submit_transaction_and_wait func & transfer coins APIs
    """
    signed_tx, _ = lcs.deserialize(signed_tx_bytes, libra.SignedTransaction)

    valid_tx_resp = tx_resp
    valid_tx_resp["result"]["transaction"][
        "public_key"
    ] = signed_tx.authenticator.public_key.value.hex()
    valid_tx_resp["result"]["transaction"][
        "signature"
    ] = signed_tx.authenticator.signature.value.hex()

    # These are the details used for building signed transaction
    sender_private_key = "11" * 32
    receiver_address = "00" * 16

    account = LibraCryptoUtils.LibraAccount.create_from_private_key(
        bytes.fromhex(sender_private_key)
    )
    valid_tx_resp["result"]["transaction"]["sender"] = account.address.hex()

    # Unknown Scripts will not have receiver/amount
    if valid_tx_resp["result"]["transaction"]["script"]["type"] != "unknown":
        valid_tx_resp["result"]["transaction"]["script"]["receiver"] = receiver_address
        valid_tx_resp["result"]["transaction"]["script"]["amount"] = 987_654_321

    return valid_tx_resp


# [TODO] Organise same func tests in a class
@pytest.fixture
def test_auth_key():
    return LibraCryptoUtils.LibraAccount.create().auth_key


@pytest.fixture
def test_address():
    return LibraCryptoUtils.LibraAccount.create().address


@pytest.fixture
def signed_transaction_bytes():
    private_key: bytes = bytes.fromhex("11" * 32)

    def _signed_transaction_bytes(type: str = "p2p"):
        if type == "p2p":
            MOCK_RECEIVER_ADDRESS: bytes = bytes.fromhex("00" * 16)
            mock_signed_tx_bytes = TransactionUtils.createSignedP2PTransaction(
                private_key,
                MOCK_RECEIVER_ADDRESS,
                # sequence
                255,
                # micro libra
                987_654_321,
                chain_id=ChainId.TESTNET,
                expiration_time=123_456_789,
                max_gas_amount=140000,
            )
        elif type == "add_currency":
            mock_signed_tx_bytes = TransactionUtils.createSignedAddCurrencyTransaction(
                private_key,
                # sequence
                255,
                chain_id=ChainId.TESTNET,
                expiration_time=123_456_789,
                identifier="Coin1",
            )
        elif type == "rotate_dual_attestation":
            mock_signed_tx_bytes = TransactionUtils.createSignedRotateDualAttestationInfoTransaction(
                new_url="https://whatever",
                new_key=bytes.fromhex("22" * 32),
                sender_private_key=private_key,
                sender_sequence=255,
                chain_id=ChainId.TESTNET,
                expiration_time=123_456_789,
            )

        return mock_signed_tx_bytes

    return _signed_transaction_bytes


@pytest.fixture
def submit_tx_response():
    def _submit_tx_response(id: int):
        return {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: 1000,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
            "result": None,
        }

    return _submit_tx_response


@pytest.fixture
def account_state_response():
    def _account_state_response(id: int, role: str = "parent"):
        resp = {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: 1000,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
            "result": {
                "address": "0e0372b4f465415dcc4c103d66f237ecb",
                "balances": [{"amount": 100000000000, "currency": "LBR"}],
                "sequence_number": 0,
                "authentication_key": "2ee7110c881f5e62d168fb8e757fead0e0372b4f465415dcc4c103d66f237ecb",
                "sent_events_key": "0100000000000000e0372b4f465415dcc4c103d66f237ecb",
                "received_events_key": "0000000000000000e0372b4f465415dcc4c103d66f237ecb",
                "delegated_key_rotation_capability": False,
                "delegated_withdrawal_capability": False,
                "is_frozen": False,
                "role": {
                    "parent_vasp": {
                        "human_name": "testnet",
                        "base_url": "https://libra.org",
                        "compliance_key": "00000000000000000000000000000000",
                        "expiration_time": 18446744073709552000,
                        "num_children": 1,
                        "base_url_rotation_events_key": "0000000000000000e0372b4f465415dcc4c103d66f237ecb",
                        "compliance_key_rotation_events_key": "0000000000000000e0372b4f465415dcc4c103d66f237ecb",
                    }
                },
            },
        }

        if role != "parent":
            if role == "child":
                resp["result"]["role"] = {  # pyre-ignore
                    "child_vasp": {"parent_vasp_address": "33" * 16}
                }
            else:
                resp["result"]["role"] = role

        return resp

    return _account_state_response


@pytest.fixture
def transaction_response():
    def _transaction_response(
        id: int = 0,
        tx_type: str = "user",
        script_type: str = "p2p",
        with_events: bool = False,
    ):
        resp: typing.Dict[str, typing.Any] = {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: 1000,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        }
        resp["result"] = get_mock_transaction(tx_type, script_type, with_events)

        return resp

    return _transaction_response


@pytest.fixture
def multiple_transaction_response():
    def _multiple_transaction_response(
        id: int = 0,
        tx_types: typing.Optional[typing.List[str]] = None,
        with_events: bool = False,
    ):
        if tx_types is None:
            tx_types = ["user"]

        resp = {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: 1000,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
            "result": [],
        }
        for tx_type in tx_types:
            resp["result"].append(  # pyre-ignore
                get_mock_transaction(tx_type, with_events=with_events)
            )

        return resp

    return _multiple_transaction_response


@pytest.fixture
def multiple_events_response():
    def _multiple_events_response(
        id: int = 0, types: typing.Optional[typing.List[str]] = None
    ):
        if types is None:
            types = ["sent"]

        resp = {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: 1000,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
            "result": [],
        }
        for type in types:
            resp["result"].append(get_mock_event(type))  # pyre-ignore

        return resp

    return _multiple_events_response


@pytest.fixture
def currency_resp():
    def _currency_resp(id: int = 0):
        return {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: 1000,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
            "result": [
                {
                    "code": "LBR",
                    "fractional_part": 1000,
                    "scaling_factor": 1000000,
                    "to_lbr_exchange_rate": 100,
                    "mint_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e530",
                    "burn_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e531",
                    "preburn_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e532",
                    "cancel_burn_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e533",
                    "exchange_rate_update_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e534",
                },
                {
                    "code": "Coin1",
                    "fractional_part": 1000,
                    "scaling_factor": 1000000,
                    "to_lbr_exchange_rate": 100,
                    "mint_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e535",
                    "burn_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e536",
                    "preburn_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e537",
                    "cancel_burn_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e538",
                    "exchange_rate_update_events_key": "0100000000000000c1fda0ec67c1b87bfb9e883e2080e539",
                },
            ],
        }

    return _currency_resp


@pytest.fixture
def metadata_resp():
    # This is to make sure that the response is not stale
    curr_time = int(time.time()) * 1_000_000

    def _metadata_resp(id: int = 0):
        return {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: 12345,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: curr_time,
            "result": {"version": 12345, "timestamp": curr_time},
        }

    return _metadata_resp


@pytest.fixture
def stale_resp():
    # this by default is set for metadata_resp, but will be used by other APIs too for checking stale resp failed
    # this should not affect the processing of other APIs as they should return ClientError because of stale response instead of further processing
    # TODO (ssinghaldev) Refactor this func to generate stale responses for various APIs
    def _metadata_resp(
        id: int = 0,
        stale_version: typing.Optional[int] = None,
        stale_timestamp_usecs: typing.Optional[int] = None,
    ):
        if not stale_version:
            # some default version value
            stale_version = 0

        if not stale_timestamp_usecs:
            stale_timestamp_usecs = (int(time.time()) * 1_000_000) // 2

        return {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: stale_version,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: stale_timestamp_usecs,
            "result": {"version": stale_version, "timestamp": stale_timestamp_usecs},
        }

    return _metadata_resp


@pytest.fixture
def json_rpc_error_resp():
    def _json_rpc_error_resp(id: int):
        return {
            "id": id,
            "jsonrpc": "2.0",
            JSONRPC_LIBRA_CHAIN_ID: 2,
            JSONRPC_LIBRA_LEDGER_VERSION: 1000,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
            "error": {"code": 4001, "data": None, "message": "Error response"},
        }

    return _json_rpc_error_resp


def test_create_libra_client_no_remote_sync_success():

    libra_client = LibraClient()

    assert libra_client._ledger_state.chain_id == DEFAULT_LIBRA_CHAIN_ID
    assert libra_client._ledger_state.blockchain_version == 0
    assert libra_client._ledger_state.blockchain_timestamp_usecs == 0


@patch("requests.Session")
def test_create_libra_client_with_remote_sync_success(mock_session, metadata_resp):

    resp = metadata_resp(0)
    mock_session.post.return_value.json.return_value = [resp]

    libra_client = LibraClient(check_server_state=True, session=mock_session)
    assert libra_client._ledger_state.chain_id == DEFAULT_LIBRA_CHAIN_ID
    assert libra_client._ledger_state.blockchain_version == resp["result"]["version"]
    assert (
        libra_client._ledger_state.blockchain_timestamp_usecs
        == resp["result"]["timestamp"]
    )


@patch("requests.Session")
def test_create_libra_client_with_remote_sync_get_metadata_network_fail(mock_session):
    mock_session.post.side_effect = RequestException

    with pytest.raises(ClientError):
        LibraClient(check_server_state=True, session=mock_session)


@patch("requests.Session")
def test_create_libra_client_with_remote_sync_get_metadata_err_resp_fail(
    mock_session, json_rpc_error_resp
):
    mock_session.post.return_value.json.return_value = [json_rpc_error_resp(0)]

    with pytest.raises(ClientError):
        LibraClient(check_server_state=True, session=mock_session)


@patch("requests.Session")
def test_create_libra_client_with_remote_sync_get_metadata_stale_resp_fail(
    mock_session, stale_resp
):
    # stale_response bcoz timestamp is negative & default is 0
    mock_session.post.return_value.json.return_value = [
        stale_resp(0, stale_timestamp_usecs=-1)
    ]

    with pytest.raises(ClientError):
        LibraClient(check_server_state=True, session=mock_session)


def test_create_libra_client_with_user_state_success():
    libra_client = LibraClient(
        chain_id=3,
        last_seen_blockchain_version=100,
        last_seen_blockchain_timestamp_usecs=1_000_000,
    )

    assert libra_client._ledger_state.chain_id == 3
    assert libra_client._ledger_state.blockchain_version == 100
    assert libra_client._ledger_state.blockchain_timestamp_usecs == 1_000_000


@patch("requests.Session")
def test_create_libra_client_with_user_state_and_check_state_success(
    mock_session, metadata_resp
):

    resp = metadata_resp(0)
    mock_session.post.return_value.json.return_value = [resp]

    # state in metadata_resp is not stale compared to last_seen state
    libra_client = LibraClient(
        check_server_state=True,
        chain_id=2,
        last_seen_blockchain_version=100,
        last_seen_blockchain_timestamp_usecs=1_000_000,
        session=mock_session,
    )

    # state should be metadata_resp state
    assert libra_client._ledger_state.chain_id == DEFAULT_LIBRA_CHAIN_ID
    assert libra_client._ledger_state.blockchain_version == resp["result"]["version"]
    assert (
        libra_client._ledger_state.blockchain_timestamp_usecs
        == resp["result"]["timestamp"]
    )


@patch("requests.Session")
def test_create_libra_client_with_user_state_and_check_state_fail(
    mock_session, stale_resp
):
    # stale_response bcoz timestamp is 1 less than last_seen_blockchain_timestamp_usecs(given below)
    mock_session.post.return_value.json.return_value = [
        stale_resp(0, stale_version=100, stale_timestamp_usecs=999_999)
    ]

    with pytest.raises(ClientError):
        LibraClient(
            check_server_state=True,
            chain_id=2,
            last_seen_blockchain_version=100,
            last_seen_blockchain_timestamp_usecs=1_000_000,
            session=mock_session,
        )


@patch("requests.Session")
def test_stale_resp_fail(mock_session, stale_resp):

    mock_session.post.return_value.json.return_value = [stale_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_metadata(
            minimum_blockchain_timestamp_usecs=int(time.time()) * 1_000_000
        )


@patch("requests.Session")
def test_mint_and_wait_success(
    mock_session, test_auth_key, transaction_response
) -> None:
    # Setting up Mock
    mock_session.post.return_value.ok = True
    mock_session.post.return_value.text = 0
    mock_session.post.return_value.json.return_value = transaction_response(0)

    libra_client = LibraClient(session=mock_session)
    libra_client.mint_and_wait(test_auth_key.hex(), 1_000_000, "LBR")

    mock_session.post.assert_called()


@patch("requests.Session")
def test_mint_and_wait_fail_faucet(mock_session, test_auth_key) -> None:
    mock_session.post.side_effect = RequestException
    with pytest.raises(ClientError):  # pyre-ignore
        libra_client = LibraClient(session=mock_session)
        libra_client.mint_and_wait(test_auth_key.hex(), 1_000_000, "LBR")


@patch("requests.Session")
def test_mint_and_wait_fail_waiting(mock_session, test_auth_key) -> None:
    mock_session.post.side_effect = get_side_effect_for_wait_failures("mint")
    with pytest.raises(ClientError):  # pyre-ignore
        libra_client = LibraClient(session=mock_session)
        libra_client.mint_and_wait(test_auth_key.hex(), 1_000_000, "LBR")


@patch("requests.Session")
def test_submit_transaction_and_wait_success(
    mock_session, signed_transaction_bytes, submit_tx_response, transaction_response
) -> None:

    # p2p tx
    signed_tx_bytes = signed_transaction_bytes()

    # TODO (ssinghaldev) Change this test to obtain equivalent signed_tx_bytes & tx_response instead of this manipulation
    # get valid tx response by changing appropriate fields in mock tx response
    valid_tx_response = get_valid_tx_response(signed_tx_bytes, transaction_response(0))

    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[submit_tx_response(0)])),
        MagicMock(json=MagicMock(return_value=[valid_tx_response])),
    ]

    libra_client = LibraClient(session=mock_session)
    status = libra_client.submit_transaction_and_wait(signed_tx_bytes)

    mock_session.post.assert_called()
    assert status == TxStatus.SUCCESS


@patch("requests.Session")
def test_submit_transaction_and_wait_fail_submitting(
    mock_session, signed_transaction_bytes
) -> None:
    mock_session.post.side_effect = RequestException

    with pytest.raises(SubmitTransactionError):  # pyre-ignore
        libra_client = LibraClient(session=mock_session)
        libra_client.submit_transaction_and_wait(signed_transaction_bytes())


@patch("requests.Session")
def test_submit_transaction_and_wait_waiting_failure_status(
    mock_session, signed_transaction_bytes, submit_tx_response, transaction_response
) -> None:

    # changing the status code to get fail response
    invalid_tx_response = transaction_response(0)
    invalid_tx_response["result"]["vm_status"] = "verification_error"

    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[submit_tx_response(0)])),
        MagicMock(json=MagicMock(return_value=[invalid_tx_response])),
    ]

    libra_client = LibraClient(session=mock_session)
    status = libra_client.submit_transaction_and_wait(signed_transaction_bytes())

    assert status == TxStatus.EXECUTION_FAIL


@patch("requests.Session")
def test_get_account_success(mock_session, test_address, account_state_response):

    mock_session.post.return_value.json.return_value = [account_state_response(0)]

    libra_client = LibraClient(session=mock_session)
    account = libra_client.get_account(test_address.hex())

    mock_session.post.assert_called()
    assert isinstance(account, LibraAccount)

    # Check various fields
    assert account.address == test_address.hex()
    assert (
        account.authentication_key
        == "2ee7110c881f5e62d168fb8e757fead0e0372b4f465415dcc4c103d66f237ecb"
    )
    assert account.balances == {"LBR": 100000000000}
    assert account.currencies == ["LBR"]
    assert account.role == "parent_vasp"
    assert account.vasp_info == {
        "human_name": "testnet",
        "base_url": "https://libra.org",
        "compliance_key": "00000000000000000000000000000000",
        "expiration_time": 18446744073709552000,
        "num_children": 1,
        "type": "parent_vasp",
        "base_url_rotation_events_key": "0000000000000000e0372b4f465415dcc4c103d66f237ecb",
        "compliance_key_rotation_events_key": "0000000000000000e0372b4f465415dcc4c103d66f237ecb",
    }


@patch("requests.Session")
def test_get_account_fail(mock_session, test_address):
    mock_session.post.side_effect = RequestException

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account(test_address.hex())


@patch("requests.Session")
def test_get_account_stale_resp_fail(mock_session, test_address, stale_resp):

    mock_session.post.return_value.json.return_value = [stale_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account(
            test_address.hex(),
            minimum_blockchain_timestamp_usecs=int(time.time()) * 1_000_000,
        )


@patch("requests.Session")
def test_p2p_tx_sucess(
    mock_session, signed_transaction_bytes, submit_tx_response, transaction_response
):
    # p2p tx
    signed_tx_bytes = signed_transaction_bytes()

    valid_tx_response = get_valid_tx_response(signed_tx_bytes, transaction_response(0))

    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[submit_tx_response(0)])),
        MagicMock(json=MagicMock(return_value=[valid_tx_response])),
    ]

    sender_private_key = "11" * 32
    receiver_address = "00" * 16

    libra_client = LibraClient(session=mock_session)
    tx_status = libra_client.transfer_coin_peer_to_peer(
        sender_private_key=sender_private_key,
        sender_sequence=255,
        currency_identifier="LBR",
        receiver=receiver_address,
        amount=987_654_321,  # micro_libra
        expiration_timestamp_secs=123_456_789,
        max_gas_amount=140000,
    )

    # generating this to verify appropriate calls are made
    account = LibraCryptoUtils.LibraAccount.create_from_private_key(
        bytes.fromhex(sender_private_key)
    )
    sender_address = account.address.hex()

    calls = [
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "submit",
                    "params": [signed_tx_bytes.hex()],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_account_transaction",
                    "params": [sender_address, 255, False],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
    ]
    mock_session.post.assert_has_calls(calls)
    assert tx_status == TxStatus.SUCCESS


@patch("requests.Session")
def test_p2p_tx_fail_submitting(mock_session):
    mock_session.post.side_effect = RequestException

    sender_private_key: bytes = "11" * 32
    receiver_address: bytes = "00" * 16

    with pytest.raises(SubmitTransactionError):
        libra_client = LibraClient(session=mock_session)
        libra_client.transfer_coin_peer_to_peer(
            sender_private_key=sender_private_key,
            sender_sequence=255,
            currency_identifier="LBR",
            receiver=receiver_address,
            amount=987_654_321,  # micro_libra
        )


@patch("requests.Session")
def test_p2p_tx_fail_waiting(mock_session, submit_tx_response, transaction_response):

    # transaction_response will not have matching signature/public key, so the tx will fail
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[submit_tx_response(0)])),
        MagicMock(json=MagicMock(return_value=[transaction_response(0)])),
    ]

    sender_private_key: bytes = "11" * 32
    receiver_address: bytes = "00" * 16

    libra_client = LibraClient(session=mock_session)
    tx_status = libra_client.transfer_coin_peer_to_peer(
        sender_private_key=sender_private_key,
        sender_sequence=255,
        currency_identifier="LBR",
        receiver=receiver_address,
        amount=987_654_321,  # micro_libra
    )

    assert tx_status == TxStatus.EXECUTION_FAIL


@patch("requests.Session")
def test_add_currency_tx_sucess(
    mock_session, signed_transaction_bytes, submit_tx_response, transaction_response
):

    signed_tx_bytes = signed_transaction_bytes("add_currency")
    valid_tx_response = get_valid_tx_response(
        signed_tx_bytes, transaction_response(0, "user", "unknown")
    )

    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[submit_tx_response(0)])),
        MagicMock(json=MagicMock(return_value=[valid_tx_response])),
    ]

    sender_private_key = "11" * 32

    # generating this to verify appropriate calls are made
    account = LibraCryptoUtils.LibraAccount.create_from_private_key(
        bytes.fromhex(sender_private_key)
    )
    sender_address = account.address.hex()

    libra_client = LibraClient(session=mock_session)
    tx_status = libra_client.add_currency_to_account(
        sender_private_key=sender_private_key,
        sender_sequence=255,
        currency_to_add="Coin1",
        expiration_timestamp_secs=123_456_789,
    )

    calls = [
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "submit",
                    "params": [signed_tx_bytes.hex()],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_account_transaction",
                    "params": [sender_address, 255, False],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
    ]
    mock_session.post.assert_has_calls(calls)

    assert tx_status == TxStatus.SUCCESS


@patch("requests.Session")
def test_add_currency_tx_fail_submitting(mock_session):
    mock_session.post.side_effect = RequestException

    sender_private_key: bytes = "11" * 32

    with pytest.raises(SubmitTransactionError):
        libra_client = LibraClient(session=mock_session)
        libra_client.add_currency_to_account(
            sender_private_key=sender_private_key,
            sender_sequence=255,
            currency_to_add="Coin1",
        )


@patch("requests.Session")
def test_add_currency_tx_fail_waiting(
    mock_session, submit_tx_response, transaction_response
):

    # transaction_response will not have matching signature/public key, so the tx will fail
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[submit_tx_response(0)])),
        MagicMock(json=MagicMock(return_value=[transaction_response(0)])),
    ]

    sender_private_key: bytes = "11" * 32

    libra_client = LibraClient(session=mock_session)
    tx_status = libra_client.add_currency_to_account(
        sender_private_key=sender_private_key,
        sender_sequence=255,
        currency_to_add="Coin1",
    )

    assert tx_status == TxStatus.EXECUTION_FAIL


@patch("requests.Session")
def test_rotate_dual_attestation_info_tx_sucess(
    mock_session, signed_transaction_bytes, submit_tx_response, transaction_response
):

    signed_tx_bytes = signed_transaction_bytes("rotate_dual_attestation")
    valid_tx_response = get_valid_tx_response(
        signed_tx_bytes, transaction_response(0, "user", "unknown")
    )

    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[submit_tx_response(0)])),
        MagicMock(json=MagicMock(return_value=[valid_tx_response])),
    ]

    sender_private_key = "11" * 32

    # generating this to verify appropriate calls are made
    account = LibraCryptoUtils.LibraAccount.create_from_private_key(
        bytes.fromhex(sender_private_key)
    )
    sender_address = account.address.hex()

    libra_client = LibraClient(session=mock_session)
    tx_status = libra_client.rotate_dual_attestation_info(
        sender_private_key=sender_private_key,
        sender_sequence=255,
        new_url="https://whatever",
        new_key=bytes.fromhex("22" * 32),
        expiration_timestamp_secs=123_456_789,
    )

    calls = [
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "submit",
                    "params": [signed_tx_bytes.hex()],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_account_transaction",
                    "params": [sender_address, 255, False],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
    ]
    mock_session.post.assert_has_calls(calls)

    assert tx_status == TxStatus.SUCCESS


@patch("requests.Session")
def test_rotate_dual_attestation_info_tx_fail_submitting(mock_session):
    mock_session.post.side_effect = RequestException

    sender_private_key: bytes = "11" * 32

    with pytest.raises(SubmitTransactionError):
        libra_client = LibraClient(session=mock_session)
        libra_client.rotate_dual_attestation_info(
            sender_private_key=sender_private_key,
            sender_sequence=255,
            new_url="https://whatever",
            new_key=bytes.fromhex("22" * 32),
        )


@patch("requests.Session")
def test_rotate_dual_attestation_info_tx_fail_waiting(
    mock_session, submit_tx_response, transaction_response
):

    # transaction_response will not have matching signature/public key, so the tx will fail
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[submit_tx_response(0)])),
        MagicMock(json=MagicMock(return_value=[transaction_response(0)])),
    ]

    sender_private_key: bytes = "11" * 32

    libra_client = LibraClient(session=mock_session)
    tx_status = libra_client.rotate_dual_attestation_info(
        sender_private_key=sender_private_key,
        sender_sequence=255,
        new_url="https://whatever",
        new_key=bytes.fromhex("22" * 32),
    )

    assert tx_status == TxStatus.EXECUTION_FAIL


@patch("requests.Session")
def test_get_account_transaction_success(
    mock_session, test_address, transaction_response
):

    mock_session.post.return_value.json.return_value = [
        transaction_response(0, "user", "p2p", True)
    ]

    libra_client = LibraClient(session=mock_session)
    tx = libra_client.get_account_transaction(test_address.hex(), 0, True)

    mock_session.post.assert_called()

    assert tx is not None
    assert isinstance(tx, LibraUserTransaction)

    # Check various fields
    assert tx.sender.hex() == "c1fda0ec67c1b87bfb9e883e2080e530"
    assert tx.sequence == 0
    assert isinstance(tx.script, LibraP2PScript)
    assert len(tx.events) == 1
    assert isinstance(tx.events[0], LibraPaymentEvent)


@patch("requests.Session")
def test_get_account_transaction_fail(mock_session, test_address):
    mock_session.post.side_effect = RequestException

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_transaction(test_address.hex(), 0, True)


@patch("requests.Session")
def test_get_account_transaction_error_resp_fail(
    mock_session, test_address, json_rpc_error_resp
):

    mock_session.post.return_value.json.return_value = [json_rpc_error_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_transaction(test_address.hex(), 0, True)


@patch("requests.Session")
def test_get_account_transaction_stale_resp_fail(
    mock_session, test_address, stale_resp
):

    mock_session.post.return_value.json.return_value = [stale_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_transaction(
            test_address.hex(),
            0,
            True,
            minimum_blockchain_timestamp_usecs=int(time.time()) * 1_000_000,
        )


@patch("requests.Session")
def test_get_transactions_success(mock_session, multiple_transaction_response):

    mock_session.post.return_value.json.return_value = [
        multiple_transaction_response(
            0, ["user", "blockmetadata", "writeset", "unknown"], True
        )
    ]

    libra_client = LibraClient(session=mock_session)
    txs = libra_client.get_transactions(0, 10, True)

    mock_session.post.assert_called()

    assert txs is not None
    assert len(txs) == 4
    assert isinstance(txs[0], LibraUserTransaction)
    assert isinstance(txs[1], LibraBlockMetadataTransaction)
    assert isinstance(txs[2], LibraWriteSetTransaction)
    assert isinstance(txs[3], LibraUnknownTransaction)


@patch("requests.Session")
def test_get_transactions_fail(mock_session):
    mock_session.post.side_effect = RequestException

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_transactions(0, 10, True)


@patch("requests.Session")
def test_get_transactions_error_resp_fail(mock_session, json_rpc_error_resp):

    mock_session.post.return_value.json.return_value = [json_rpc_error_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_transactions(0, 10, True)


@patch("requests.Session")
def test_get_transactions_stale_resp_fail(mock_session, stale_resp):

    mock_session.post.return_value.json.return_value = [stale_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_transactions(
            0, 10, True, minimum_blockchain_timestamp_usecs=int(time.time()) * 1_000_000
        )


@patch("requests.Session")
def test_get_account_sent_events_success(
    mock_session, test_address, account_state_response, multiple_events_response
):
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[account_state_response(0)])),
        MagicMock(
            json=MagicMock(return_value=[multiple_events_response(0, ["sent", "sent"])])
        ),
    ]

    libra_client = LibraClient(session=mock_session)
    events = libra_client.get_account_sent_events(test_address.hex(), 0, 10)

    calls = [
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_account",
                    "params": [test_address.hex()],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_events",
                    "params": [
                        account_state_response(0)["result"]["sent_events_key"],
                        0,
                        10,
                    ],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
    ]

    mock_session.post.assert_has_calls(calls)

    assert len(events) == 2
    assert isinstance(events[0], LibraPaymentEvent) and isinstance(
        events[1], LibraPaymentEvent
    )
    assert events[0].type == "sentpayment" and events[1].type == "sentpayment"

    sent_mock_event = get_mock_event("sent")
    assert events[0].receiver.hex() == sent_mock_event["data"]["receiver"]
    assert events[0].sender.hex() == sent_mock_event["data"]["sender"]
    assert events[0].currency == sent_mock_event["data"]["amount"]["currency"]

    assert events[1].receiver.hex() == sent_mock_event["data"]["receiver"]
    assert events[1].sender.hex() == sent_mock_event["data"]["sender"]
    assert events[1].currency == sent_mock_event["data"]["amount"]["currency"]


@patch("requests.Session")
def test_get_account_sent_events_fail(mock_session, test_address):
    mock_session.post.side_effect = RequestException

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_sent_events(test_address.hex(), 0, 10)


@patch("requests.Session")
def test_get_account_sent_events_error_resp_fail(
    mock_session, test_address, account_state_response, json_rpc_error_resp
):
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[account_state_response(0)])),
        MagicMock(json=MagicMock(return_value=[json_rpc_error_resp(0)])),
    ]
    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_sent_events(test_address.hex(), 0, 10)


@patch("requests.Session")
def test_get_account_sent_events_other_resp_fail(
    mock_session, test_address, account_state_response, multiple_events_response
):
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[account_state_response(0)])),
        # getting received events in response. Should raise exception
        MagicMock(
            json=MagicMock(
                return_value=[multiple_events_response(0, ["sent", "received"])]
            )
        ),
    ]
    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_sent_events(test_address.hex(), 0, 10)


@patch("requests.Session")
def test_get_account_sent_events_stale_resp_fail(
    mock_session, test_address, stale_resp
):

    mock_session.post.return_value.json.return_value = [stale_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_sent_events(
            test_address.hex(),
            0,
            10,
            minimum_blockchain_timestamp_usecs=int(time.time()) * 1_000_000,
        )


@patch("requests.Session")
def test_get_account_received_events_success(
    mock_session, test_address, account_state_response, multiple_events_response
):
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[account_state_response(0)])),
        MagicMock(
            json=MagicMock(
                return_value=[multiple_events_response(0, ["received", "received"])]
            )
        ),
    ]

    libra_client = LibraClient(session=mock_session)
    events = libra_client.get_account_received_events(test_address.hex(), 0, 10)

    calls = [
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_account",
                    "params": [test_address.hex()],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_events",
                    "params": [
                        account_state_response(0)["result"]["received_events_key"],
                        0,
                        10,
                    ],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
    ]

    mock_session.post.assert_has_calls(calls)

    assert len(events) == 2
    assert isinstance(events[0], LibraPaymentEvent) and isinstance(
        events[1], LibraPaymentEvent
    )
    assert events[0].type == "receivedpayment" and events[1].type == "receivedpayment"

    received_mock_event = get_mock_event("received")
    assert events[0].sender.hex() == received_mock_event["data"]["sender"]
    assert events[0].receiver.hex() == received_mock_event["data"]["receiver"]
    assert events[0].currency == received_mock_event["data"]["amount"]["currency"]

    assert events[1].sender.hex() == received_mock_event["data"]["sender"]
    assert events[1].receiver.hex() == received_mock_event["data"]["receiver"]
    assert events[1].currency == received_mock_event["data"]["amount"]["currency"]


@patch("requests.Session")
def test_get_account_received_events_fail(mock_session, test_address):
    mock_session.post.side_effect = RequestException

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_received_events(test_address.hex(), 0, 10)


@patch("requests.Session")
def test_get_account_received_events_error_resp_fail(
    mock_session, test_address, account_state_response, json_rpc_error_resp
):
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[account_state_response(0)])),
        MagicMock(json=MagicMock(return_value=[json_rpc_error_resp(0)])),
    ]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_received_events(test_address.hex(), 0, 10)


@patch("requests.Session")
def test_get_account_received_events_other_resp_fail(
    mock_session, test_address, account_state_response, multiple_events_response
):
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[account_state_response(0)])),
        # getting sent events in response. Should raise exception
        MagicMock(
            json=MagicMock(
                return_value=[multiple_events_response(0, ["sent", "received"])]
            )
        ),
    ]
    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_received_events(test_address.hex(), 0, 10)


@patch("requests.Session")
def test_get_account_received_events_stale_resp_fail(
    mock_session, test_address, stale_resp
):

    mock_session.post.return_value.json.return_value = [stale_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_account_received_events(
            test_address.hex(),
            0,
            10,
            minimum_blockchain_timestamp_usecs=int(time.time()) * 1_000_000,
        )


@patch("requests.Session")
def test_get_currencies_success(mock_session, currency_resp):

    mock_session.post.return_value.json.return_value = [currency_resp(0)]

    libra_client = LibraClient(session=mock_session)
    currencies_info = libra_client.get_currencies()

    mock_session.post.assert_called_once()
    assert len(currencies_info) == 2
    assert currencies_info[0].code == "LBR"
    assert currencies_info[1].code == "Coin1"


@patch("requests.Session")
def test_get_currencies_fail(mock_session, test_address):
    mock_session.post.side_effect = RequestException

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_currencies()


@patch("requests.Session")
def test_get_currencies_error_resp_fail(mock_session, json_rpc_error_resp):
    mock_session.post.return_value.json.return_value = [json_rpc_error_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_currencies()


@patch("requests.Session")
def test_get_currencies_stale_resp_fail(mock_session, stale_resp):

    mock_session.post.return_value.json.return_value = [stale_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_currencies(
            minimum_blockchain_timestamp_usecs=int(time.time()) * 1_000_000
        )


@patch("requests.Session")
def test_get_metadata_success(mock_session, metadata_resp):

    resp = metadata_resp(0)
    mock_session.post.return_value.json.return_value = [resp]

    libra_client = LibraClient(session=mock_session)
    metadata = libra_client.get_metadata()

    mock_session.post.assert_called_once()
    assert metadata.version == resp["result"]["version"]
    assert metadata.timestamp_usecs == resp["result"]["timestamp"]


@patch("requests.Session")
def test_get_metadata_fail(mock_session):
    mock_session.post.side_effect = RequestException

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_metadata()


@patch("requests.Session")
def test_get_metadata_err_resp_fail(mock_session, json_rpc_error_resp):
    mock_session.post.return_value.json.return_value = [json_rpc_error_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_metadata()


@patch("requests.Session")
def test_get_metadata_stale_resp_fail(mock_session, stale_resp):

    mock_session.post.return_value.json.return_value = [stale_resp(0)]

    with pytest.raises(ClientError):
        libra_client = LibraClient(session=mock_session)
        libra_client.get_metadata(
            minimum_blockchain_timestamp_usecs=int(time.time()) * 1_000_000
        )


@patch("requests.Session")
def test_get_root_vasp_account_input_parent_success(
    mock_session, test_address, account_state_response
):

    mock_session.post.return_value.json.return_value = [account_state_response(0)]

    libra_client = LibraClient(session=mock_session)
    account = libra_client.get_root_vasp_account(test_address.hex())

    calls = [
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_account",
                    "params": [test_address.hex()],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        )
    ]
    mock_session.post.assert_has_calls(calls)
    assert account.role == "parent_vasp"


@patch("requests.Session")
def test_get_root_vasp_account_input_child_success(
    mock_session, test_address, account_state_response
):
    child_accnt_resp = account_state_response(0, "child")
    parent_accnt_resp = account_state_response(0, "parent")
    parent_vasp_addr = child_accnt_resp["result"]["role"]["child_vasp"][
        "parent_vasp_address"
    ]
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[child_accnt_resp])),
        MagicMock(json=MagicMock(return_value=[parent_accnt_resp])),
    ]

    libra_client = LibraClient(session=mock_session)
    account = libra_client.get_root_vasp_account(test_address.hex())

    calls = [
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_account",
                    "params": [test_address.hex()],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
        call(
            DEFAULT_JSON_RPC_SERVER,
            json=[
                {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "get_account",
                    "params": [parent_vasp_addr],
                }
            ],
            timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
        ),
    ]

    mock_session.post.assert_has_calls(calls)
    assert account.role == "parent_vasp"


@patch("requests.Session")
def test_get_root_vasp_account_fail(mock_session, test_address, account_state_response):
    mock_session.post.side_effect = [
        MagicMock(json=MagicMock(return_value=[account_state_response(0, "child")])),
        RequestException,
    ]

    libra_client = LibraClient(session=mock_session)
    with pytest.raises(ClientError):
        libra_client.get_root_vasp_account(test_address.hex())
