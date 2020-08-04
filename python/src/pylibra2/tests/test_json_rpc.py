from unittest.mock import patch

import pytest
from calibra.lib.clients.pylibra2 import (
    DEFAULT_CONNECT_TIMEOUT_SECS,
    DEFAULT_TIMEOUT_SECS,
)
from calibra.lib.clients.pylibra2._config import (
    JSONRPC_LIBRA_CHAIN_ID,
    JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS,
    JSONRPC_LIBRA_LEDGER_VERSION,
)
from calibra.lib.clients.pylibra2.json_rpc.request import (
    InvalidServerResponse,
    JsonRpcBatch,
    JsonRpcClient,
)
from calibra.lib.clients.pylibra2.json_rpc.types import (
    AccountStateResponse,
    AmountData,
    CurrencyInfo,
    CurrencyResponse,
    Event,
    MetadataResponse,
    ParentVASP,
    PeerToPeerTransferScript,
    SentPaymentEvent,
    TransactionResponse,
    UnknownTransaction,
    UserTransaction,
    WriteSetTransaction,
)


def get_valid_result_submit_response(id: int):
    return {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": None,
    }


def get_valid_result_account_state_response(id: int):
    return {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": {
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
                }
            },
        },
    }


def get_valid_result_metadata_response(id: int):
    return {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": {"version": 25, "timestamp": 1593197593},
    }


def get_valid_result_currency_response(id: int):
    return {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": [
            {"code": "LBR", "fractional_part": 1000, "scaling_factor": 1000000},
            {"code": "Coin1", "fractional_part": 1000, "scaling_factor": 1000000},
        ],
    }


def get_invalid_result_response(id: int):
    return {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": {"incorrect_key": "random_value"},
    }


def get_valid_result_tx_response(
    id: int, tx_type: str = "user", with_events: bool = False
):

    resp = {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": {
            "transaction": {
                "expiration_time": 1590680747,
                "gas_unit_price": 0,
                "gas_currency": "LBR",
                "max_gas_amount": 1000000,
                "public_key": "500a9002995e1af93bbdaf977385ed507b174bb3dc6936efd72612d56198a19d",
                "script": {
                    "amount": 10000000,
                    "auth_key_prefix": "6484f428e88bba93de5053e051acb6ec",
                    "metadata": "",
                    "metadata_signature": "",
                    "receiver": "4ac94d88e90acd4cf0294e898e421e94",
                    "type": "peer_to_peer_transaction",
                },
                "script_hash": "c8bc3dda60e9662965b3223c22e3d3e3e7b6f698cf1a6930a449eb99daa35e7c",
                "sender": "c1fda0ec67c1b87bfb9e883e2080e530",
                "sequence_number": 0,
                "signature": "fe335285e5d87db25f86041d033414bfdf77ddae6f0dfbdc65ff4f5965ff810ef9c85ce00ede0820ce0cf5903f9ab3e93fa6e49bbf770aba9b083a985361fa01",
                "signature_scheme": "Scheme::Ed25519",
                "type": "user",
            },
            "events": [],
            "version": 4433485,
            "vm_status": 4001,
            "gas_used": 0,
        },
    }

    if tx_type != "user":
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

        resp["result"].update(tx_dict)  # pyre-ignore

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
                        "receiver": "4ac94d88e90acd4cf0294e898e421e94",
                        "type": "sentpayment",
                    },
                }
            ]
        }

        resp["result"].update(event_dict)

    return resp


def get_valid_result_multiple_tx_response(
    id: int, num_responses: int, with_events: bool = False
):
    resp = {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": [],
    }
    tx_dict = {
        "transaction": {
            "expiration_time": 1590680747,
            "gas_unit_price": 0,
            "gas_currency": "LBR",
            "max_gas_amount": 1000000,
            "public_key": "500a9002995e1af93bbdaf977385ed507b174bb3dc6936efd72612d56198a19d",
            "script": {
                "amount": 10000000,
                "auth_key_prefix": "6484f428e88bba93de5053e051acb6ec",
                "metadata": "",
                "metadata_signature": "",
                "receiver": "4ac94d88e90acd4cf0294e898e421e94",
                "type": "peer_to_peer_transaction",
            },
            "script_hash": "c8bc3dda60e9662965b3223c22e3d3e3e7b6f698cf1a6930a449eb99daa35e7c",
            "sender": "c1fda0ec67c1b87bfb9e883e2080e530",
            "sequence_number": 0,
            "signature": "fe335285e5d87db25f86041d033414bfdf77ddae6f0dfbdc65ff4f5965ff810ef9c85ce00ede0820ce0cf5903f9ab3e93fa6e49bbf770aba9b083a985361fa01",
            "signature_scheme": "Scheme::Ed25519",
            "type": "user",
        },
        "events": [],
        "version": 4433485,
        "vm_status": 4001,
        "gas_used": 0,
    }

    for _ in range(num_responses):
        resp["result"].append(tx_dict)  # pyre-ignore

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
                        "receiver": "4ac94d88e90acd4cf0294e898e421e94",
                        "type": "sentpayment",
                    },
                }
            ]
        }

        for i in range(num_responses):
            resp["result"][i].update(event_dict)  # pyre-ignore

    return resp


# Special function to test whether writeset/unknown transactions are handled correctly
def get_writeset_unknown_transaction_response(id: int):
    resp = {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": [
            {
                "transaction": {"type": "writeset"},
                "events": [],
                "version": 4433485,
                "vm_status": 4001,
                "gas_used": 0,
            },
            {
                "transaction": {"type": "unknown"},
                "events": [],
                "version": 4433485,
                "vm_status": 4001,
                "gas_used": 0,
            },
        ],
    }

    return resp


def get_valid_result_multiple_events_response(
    id: int, event_key: str, num_responses: int
):
    resp = {
        "id": id,
        "jsonrpc": "2.0",
        JSONRPC_LIBRA_CHAIN_ID: 2,
        JSONRPC_LIBRA_LEDGER_VERSION: 1000,
        JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS: 100000,
        "result": [],
    }
    event_dict = {
        "key": event_key,
        "sequence_number": 0,
        "transaction_version": 4433485,
        "data": {
            "amount": {"amount": 10000000, "currency": "LBR"},
            "metadata": "",
            "receiver": "4ac94d88e90acd4cf0294e898e421e94",
            "type": "sentpayment",
        },
    }

    for _ in range(num_responses):
        resp["result"].append(event_dict)  # pyre-ignore

    return resp


def test_json_rpc_batch():
    batch = JsonRpcBatch()

    batch.add_get_metadata_request()
    batch.add_submit_request("abcdef0123456789")

    json_rpc_obj = batch.get_json_rpc_request_object()

    # Methods are added in order
    assert json_rpc_obj[0]["method"] == "get_metadata"
    assert json_rpc_obj[1]["method"] == "submit"

    # Params are correctly added
    assert json_rpc_obj[0]["params"] == ["null"]
    assert json_rpc_obj[1]["params"] == ["abcdef0123456789"]

    # Ids are different
    assert json_rpc_obj[0]["id"] != json_rpc_obj[1]["id"]


@patch("requests.Session")
def test_json_rpc_client(mock_session):
    batch = JsonRpcBatch()
    batch.add_submit_request("abcdef0123456789")

    mock_session.post.return_value.json.return_value = [
        get_valid_result_submit_response(0)
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "submit",
                "params": ["abcdef0123456789"],
            }
        ],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )


@patch("requests.Session")
def test_multiple_requests_success(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_metadata_request()
    batch.add_get_account_request("11" * 16)

    # Note: Changed the order to verify that the response is sorted according to request
    mock_session.post.return_value.json.return_value = [
        get_valid_result_account_state_response(1),
        get_valid_result_metadata_response(0),
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    response_obj = client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[
            {"jsonrpc": "2.0", "id": 0, "method": "get_metadata", "params": ["null"]},
            {"jsonrpc": "2.0", "id": 1, "method": "get_account", "params": ["11" * 16]},
        ],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )

    assert response_obj.chain_id == 2
    assert response_obj.version == 1000
    assert response_obj.timestamp_usecs == 100000
    assert isinstance(response_obj.responses[0], MetadataResponse)
    assert isinstance(response_obj.responses[1], AccountStateResponse)


@patch("requests.session")
def test_multiple_requests_fail(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_metadata_request()
    batch.add_get_account_request("11" * 16)

    mock_session.post.return_value.json.return_value = [
        get_valid_result_metadata_response(0),
        get_invalid_result_response(1),
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    with pytest.raises(InvalidServerResponse):
        client.execute(batch)


def test_invalid_address_add_account_state_request():
    batch = JsonRpcBatch()
    with pytest.raises(ValueError):
        batch.add_get_account_request("11" * 32)


def test_invalid_event_key_get_events_request():
    batch = JsonRpcBatch()
    with pytest.raises(ValueError):
        batch.add_get_events_request("11" * 32, 0, 2)


@patch("requests.Session")
def test_account_state_response_success(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_account_request("11" * 16)

    mock_session.post.return_value.json.return_value = [
        get_valid_result_account_state_response(0)
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    response_obj = client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[
            {"jsonrpc": "2.0", "id": 0, "method": "get_account", "params": ["11" * 16]}
        ],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )

    assert response_obj.responses[0] == AccountStateResponse(
        balances=[AmountData(amount=100000000000, currency="LBR")],
        sequence_number=0,
        authentication_key="2ee7110c881f5e62d168fb8e757fead0e0372b4f465415dcc4c103d66f237ecb",
        sent_events_key="0100000000000000e0372b4f465415dcc4c103d66f237ecb",
        received_events_key="0000000000000000e0372b4f465415dcc4c103d66f237ecb",
        delegated_key_rotation_capability=False,
        delegated_withdrawal_capability=False,
        is_frozen=False,
        role={
            "parent_vasp": ParentVASP(
                human_name="testnet",
                base_url="https://libra.org",
                compliance_key="00000000000000000000000000000000",
                expiration_time=18446744073709552000,
                num_children=1,
            )
        },
    )


@patch("requests.Session")
def test_account_state_response_fail(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_account_request("11" * 16)

    mock_session.post.return_value.json.return_value = [get_invalid_result_response(0)]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    with pytest.raises(InvalidServerResponse):
        client.execute(batch)


@patch("requests.Session")
def test_get_currency_success(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_currencies_request()

    mock_session.post.return_value.json.return_value = [
        get_valid_result_currency_response(0)
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    response_obj = client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[{"jsonrpc": "2.0", "id": 0, "method": "get_currencies", "params": []}],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )

    assert response_obj.responses[0] == CurrencyResponse(
        currencies_info=[
            CurrencyInfo(code="LBR", fractional_part=1000, scaling_factor=1000000),
            CurrencyInfo(code="Coin1", fractional_part=1000, scaling_factor=1000000),
        ]
    )


@patch("requests.Session")
def test_get_currency_fail(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_currencies_request()

    mock_session.post.return_value.json.return_value = [get_invalid_result_response(0)]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    with pytest.raises(InvalidServerResponse):
        client.execute(batch)


@patch("requests.Session")
def test_get_account_transaction_with_events_success(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_trasaction_by_accnt_seq_request("11" * 16, 0, True)

    mock_session.post.return_value.json.return_value = [
        get_valid_result_tx_response(0, with_events=True)
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    response_obj = client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "get_account_transaction",
                "params": ["11" * 16, 0, True],
            }
        ],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )

    assert response_obj.responses[0] == TransactionResponse(
        transaction=UserTransaction(
            expiration_time=1590680747,
            gas_unit_price=0,
            gas_currency="LBR",
            max_gas_amount=1000000,
            public_key="500a9002995e1af93bbdaf977385ed507b174bb3dc6936efd72612d56198a19d",
            script=PeerToPeerTransferScript(
                amount=10000000,
                auth_key_prefix="6484f428e88bba93de5053e051acb6ec",
                metadata="",
                metadata_signature="",
                receiver="4ac94d88e90acd4cf0294e898e421e94",
                type="peer_to_peer_transaction",
            ),
            script_hash="c8bc3dda60e9662965b3223c22e3d3e3e7b6f698cf1a6930a449eb99daa35e7c",
            sender="c1fda0ec67c1b87bfb9e883e2080e530",
            sequence_number=0,
            signature="fe335285e5d87db25f86041d033414bfdf77ddae6f0dfbdc65ff4f5965ff810ef9c85ce00ede0820ce0cf5903f9ab3e93fa6e49bbf770aba9b083a985361fa01",
            signature_scheme="Scheme::Ed25519",
            type="user",
        ),
        events=[
            Event(
                key="0100000000000000c1fda0ec67c1b87bfb9e883e2080e530",
                sequence_number=0,
                transaction_version=4433485,
                data=SentPaymentEvent(
                    amount=AmountData(amount=10000000, currency="LBR"),
                    metadata="",
                    receiver="4ac94d88e90acd4cf0294e898e421e94",
                    type="sentpayment",
                ),
            )
        ],
        version=4433485,
        vm_status=4001,
        gas_used=0,
    )


@patch("requests.Session")
def test_get_account_transaction_without_events_success(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_trasaction_by_accnt_seq_request("11" * 16, 0, False)

    mock_session.post.return_value.json.return_value = [get_valid_result_tx_response(0)]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    response_obj = client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "get_account_transaction",
                "params": ["11" * 16, 0, False],
            }
        ],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )

    assert response_obj.responses[0] == TransactionResponse(
        transaction=UserTransaction(
            expiration_time=1590680747,
            gas_unit_price=0,
            gas_currency="LBR",
            max_gas_amount=1000000,
            public_key="500a9002995e1af93bbdaf977385ed507b174bb3dc6936efd72612d56198a19d",
            script=PeerToPeerTransferScript(
                amount=10000000,
                auth_key_prefix="6484f428e88bba93de5053e051acb6ec",
                metadata="",
                metadata_signature="",
                receiver="4ac94d88e90acd4cf0294e898e421e94",
                type="peer_to_peer_transaction",
            ),
            script_hash="c8bc3dda60e9662965b3223c22e3d3e3e7b6f698cf1a6930a449eb99daa35e7c",
            sender="c1fda0ec67c1b87bfb9e883e2080e530",
            sequence_number=0,
            signature="fe335285e5d87db25f86041d033414bfdf77ddae6f0dfbdc65ff4f5965ff810ef9c85ce00ede0820ce0cf5903f9ab3e93fa6e49bbf770aba9b083a985361fa01",
            signature_scheme="Scheme::Ed25519",
            type="user",
        ),
        events=[],
        version=4433485,
        vm_status=4001,
        gas_used=0,
    )


@patch("requests.Session")
def test_get_account_transaction_fail(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_trasaction_by_accnt_seq_request("11" * 16, 0, True)

    mock_session.post.return_value.json.return_value = [get_invalid_result_response(0)]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    with pytest.raises(InvalidServerResponse):
        client.execute(batch)


@patch("requests.Session")
def test_get_account_transaction_non_user_response_fail(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_trasaction_by_accnt_seq_request("11" * 16, 0, True)

    mock_session.post.return_value.json.return_value = [
        get_valid_result_tx_response(0, "writeset")
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    with pytest.raises(InvalidServerResponse):
        client.execute(batch)


@patch("requests.Session")
def test_get_transactions_success(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_transactions_by_range_request(0, 2, False)

    mock_session.post.return_value.json.return_value = [
        get_valid_result_multiple_tx_response(0, 2)
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    response_obj = client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "get_transactions",
                "params": [0, 2, False],
            }
        ],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )

    assert response_obj.responses[0] == [
        TransactionResponse(
            transaction=UserTransaction(
                expiration_time=1590680747,
                gas_unit_price=0,
                gas_currency="LBR",
                max_gas_amount=1000000,
                public_key="500a9002995e1af93bbdaf977385ed507b174bb3dc6936efd72612d56198a19d",
                script=PeerToPeerTransferScript(
                    amount=10000000,
                    auth_key_prefix="6484f428e88bba93de5053e051acb6ec",
                    metadata="",
                    metadata_signature="",
                    receiver="4ac94d88e90acd4cf0294e898e421e94",
                    type="peer_to_peer_transaction",
                ),
                script_hash="c8bc3dda60e9662965b3223c22e3d3e3e7b6f698cf1a6930a449eb99daa35e7c",
                sender="c1fda0ec67c1b87bfb9e883e2080e530",
                sequence_number=0,
                signature="fe335285e5d87db25f86041d033414bfdf77ddae6f0dfbdc65ff4f5965ff810ef9c85ce00ede0820ce0cf5903f9ab3e93fa6e49bbf770aba9b083a985361fa01",
                signature_scheme="Scheme::Ed25519",
                type="user",
            ),
            events=[],
            version=4433485,
            vm_status=4001,
            gas_used=0,
        ),
        TransactionResponse(
            transaction=UserTransaction(
                expiration_time=1590680747,
                gas_unit_price=0,
                gas_currency="LBR",
                max_gas_amount=1000000,
                public_key="500a9002995e1af93bbdaf977385ed507b174bb3dc6936efd72612d56198a19d",
                script=PeerToPeerTransferScript(
                    amount=10000000,
                    auth_key_prefix="6484f428e88bba93de5053e051acb6ec",
                    metadata="",
                    metadata_signature="",
                    receiver="4ac94d88e90acd4cf0294e898e421e94",
                    type="peer_to_peer_transaction",
                ),
                script_hash="c8bc3dda60e9662965b3223c22e3d3e3e7b6f698cf1a6930a449eb99daa35e7c",
                sender="c1fda0ec67c1b87bfb9e883e2080e530",
                sequence_number=0,
                signature="fe335285e5d87db25f86041d033414bfdf77ddae6f0dfbdc65ff4f5965ff810ef9c85ce00ede0820ce0cf5903f9ab3e93fa6e49bbf770aba9b083a985361fa01",
                signature_scheme="Scheme::Ed25519",
                type="user",
            ),
            events=[],
            version=4433485,
            vm_status=4001,
            gas_used=0,
        ),
    ]


@patch("requests.Session")
def test_get_transactions_fail(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_transactions_by_range_request(0, 2, False)

    mock_session.post.return_value.json.return_value = [get_invalid_result_response(0)]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    with pytest.raises(InvalidServerResponse):
        client.execute(batch)


@patch("requests.Session")
def test_writeset_unknown_tx_success(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_transactions_by_range_request(0, 2, False)

    mock_session.post.return_value.json.return_value = [
        get_writeset_unknown_transaction_response(0)
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    response_obj = client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "get_transactions",
                "params": [0, 2, False],
            }
        ],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )

    assert response_obj.responses[0] == [
        TransactionResponse(
            transaction=WriteSetTransaction(type="writeset"),
            events=[],
            version=4433485,
            vm_status=4001,
            gas_used=0,
        ),
        TransactionResponse(
            transaction=UnknownTransaction(type="unknown"),
            events=[],
            version=4433485,
            vm_status=4001,
            gas_used=0,
        ),
    ]


@patch("requests.Session")
def test_get_events_success(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_events_request("11" * 24, 0, 2)

    mock_session.post.return_value.json.return_value = [
        get_valid_result_multiple_events_response(
            id=0, event_key="11" * 24, num_responses=2
        )
    ]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    response_obj = client.execute(batch)

    mock_session.post.assert_called_once_with(
        "https://dummyurl.com",
        json=[
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "get_events",
                "params": ["11" * 24, 0, 2],
            }
        ],
        timeout=(DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
    )

    assert response_obj.responses[0] == [
        Event(
            key="11" * 24,
            sequence_number=0,
            transaction_version=4433485,
            data=SentPaymentEvent(
                amount=AmountData(amount=10000000, currency="LBR"),
                metadata="",
                receiver="4ac94d88e90acd4cf0294e898e421e94",
                type="sentpayment",
            ),
        ),
        Event(
            key="11" * 24,
            sequence_number=0,
            transaction_version=4433485,
            data=SentPaymentEvent(
                amount=AmountData(amount=10000000, currency="LBR"),
                metadata="",
                receiver="4ac94d88e90acd4cf0294e898e421e94",
                type="sentpayment",
            ),
        ),
    ]


@patch("requests.Session")
def test_get_events_fail(mock_session):
    batch = JsonRpcBatch()
    batch.add_get_events_request("11" * 24, 0, 2)

    mock_session.post.return_value.json.return_value = [get_invalid_result_response(0)]

    client = JsonRpcClient("https://dummyurl.com", mock_session)
    with pytest.raises(InvalidServerResponse):
        client.execute(batch)
