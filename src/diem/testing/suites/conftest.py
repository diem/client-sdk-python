# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from ... import testnet, jsonrpc, identifier, offchain
from .. import LocalAccount
from ..miniwallet import RestClient, AppConfig, AccountResource, ServerConfig, App
from ..miniwallet.app import PENDING_INBOUND_ACCOUNT_ID
from .envs import (
    target_url,
    is_self_check,
    dmw_stub_server,
    dmw_stub_diem_account_config,
    dmw_stub_diem_account_hrp,
)
from typing import Optional, Tuple, Dict, Any, Generator
from dataclasses import asdict
import pytest, json, uuid, requests, time, warnings


@pytest.fixture(scope="package")
def target_client(diem_client: jsonrpc.Client) -> RestClient:
    if is_self_check():
        conf = AppConfig(name="target-wallet")
        print("self-checking, launch target app with config %s" % conf)
        conf.start(diem_client)
        return conf.create_client()
    print("target wallet server url: %s" % target_url())
    return RestClient(name="target-wallet-client", server_url=target_url()).with_retry()


@pytest.fixture(scope="package")
def diem_client() -> jsonrpc.Client:
    print("Diem JSON-RPC URL: %s" % testnet.JSON_RPC_URL)
    print("Diem Testnet Faucet URL: %s" % testnet.FAUCET_URL)
    return testnet.create_client()


@pytest.fixture(scope="package")
def stub_config(start_stub_wallet: Tuple[AppConfig, App]) -> AppConfig:
    return start_stub_wallet[0]


@pytest.fixture(scope="package")
def stub_wallet_app(start_stub_wallet: Tuple[AppConfig, App]) -> App:
    return start_stub_wallet[1]


@pytest.fixture(scope="package")
def start_stub_wallet(diem_client: jsonrpc.Client) -> Tuple[AppConfig, App]:
    conf = AppConfig(name="stub-wallet", server_conf=ServerConfig(**dmw_stub_server()))
    account_conf = dmw_stub_diem_account_config()
    if account_conf:
        print("loads stub account config: %s" % account_conf)
        conf.account_config = json.loads(account_conf)
    hrp = dmw_stub_diem_account_hrp()
    if hrp:
        conf.account_config["hrp"] = hrp
    print("Start stub app with config %s" % conf)
    app, _ = conf.start(diem_client)
    return (conf, app)


@pytest.fixture(autouse=True)
def log_stub_account_info(stub_config: AppConfig, diem_client: jsonrpc.Client) -> Generator[None, None, None]:
    yield
    stub_config.logger.info("=== stub wallet ParentVASP account info ===")
    data = diem_client.get_account(stub_config.account.account_address)
    stub_config.logger.info(data)

    stub_config.logger.info("=== stub wallet ChildVASP accounts info ===")
    for i, child in enumerate(stub_config.child_accounts):
        data = diem_client.get_account(child.account_address)
        stub_config.logger.info("--- ChildVASP account %s ---", i + 1)
        stub_config.logger.info(data)


@pytest.fixture(scope="package")
def stub_client(stub_config: AppConfig) -> RestClient:
    return stub_config.create_client()


@pytest.fixture
def hrp(stub_config: AppConfig) -> str:
    return stub_config.account.hrp


@pytest.fixture
def currency() -> str:
    return testnet.TEST_CURRENCY_CODE


@pytest.fixture
def travel_rule_threshold(diem_client: jsonrpc.Client) -> int:
    # todo: convert the limit base on currency
    return diem_client.get_metadata().dual_attestation_limit


@pytest.fixture
def stub_wallet_pending_income_account(stub_client: RestClient) -> AccountResource:
    """MiniWallet stub saves the payment without account information (subaddress / reference id)
    into a pending income account before processing it.
    """

    return AccountResource(id=PENDING_INBOUND_ACCOUNT_ID, client=stub_client)


@pytest.fixture(autouse=True)
def log_stub_wallet_pending_income_account(
    stub_wallet_pending_income_account: AccountResource,
) -> Generator[None, None, None]:
    yield
    stub_wallet_pending_income_account.log_events()


def send_request_json(
    diem_client: jsonrpc.Client,
    sender_account: LocalAccount,
    sender_address: Optional[str],
    receiver_address: str,
    request_json: str,
    hrp: str,
    x_request_id: Optional[str] = str(uuid.uuid4()),
    request_body: Optional[bytes] = None,
) -> Tuple[int, offchain.CommandResponseObject]:
    headers = {}
    if x_request_id:
        headers[offchain.http_header.X_REQUEST_ID] = x_request_id
    if sender_address:
        headers[offchain.http_header.X_REQUEST_SENDER_ADDRESS] = sender_address

    account_address, _ = identifier.decode_account(receiver_address, hrp)
    base_url, public_key = diem_client.get_base_url_and_compliance_key(account_address)
    if request_body is None:
        request_body = offchain.jws.serialize_string(request_json, sender_account.compliance_key.sign)
    resp = requests.Session().post(
        f"{base_url.rstrip('/')}/v2/command",
        data=request_body,
        headers=headers,
    )

    cmd_resp_obj = offchain.jws.deserialize(resp.content, offchain.CommandResponseObject, public_key.verify)

    return (resp.status_code, cmd_resp_obj)


def payment_command_request_sample(
    sender_address: str, sender_kyc_data: offchain.KycDataObject, receiver_address: str, currency: str, amount: int
) -> Dict[str, Any]:
    """Creates a `PaymentCommand` initial state request JSON object (dictionary).

    Sender address is from the stub wallet application.

    Receiver address is from the target wallet application.
    """

    return {
        "_ObjectType": "CommandRequestObject",
        "cid": str(uuid.uuid4()),
        "command_type": "PaymentCommand",
        "command": {
            "_ObjectType": "PaymentCommand",
            "payment": {
                "reference_id": str(uuid.uuid4()),
                "sender": {
                    "address": sender_address,
                    "status": {"status": "needs_kyc_data"},
                    "kyc_data": asdict(sender_kyc_data),
                },
                "receiver": {
                    "address": receiver_address,
                    "status": {"status": "none"},
                },
                "action": {
                    "amount": amount,
                    "currency": currency,
                    "action": "charge",
                    "timestamp": int(time.time()),
                },
            },
        },
    }


def assert_response_error(
    resp: offchain.CommandResponseObject, code: str, err_type: str, field: Optional[str] = None
) -> None:
    assert resp.error, resp
    try:
        assert resp.error.type == err_type
        assert resp.error.code == code
        assert resp.error.field == field
    except AssertionError as e:
        warnings.warn(str(e), Warning)


def set_field(dic: Dict[str, Any], field: str, value: Any) -> None:  # pyre-ignore
    path = field.split(".")
    for f in path[0 : len(path) - 1]:
        if f not in dic:
            dic[f] = {}
        dic = dic[f]

    dic[path[len(path) - 1]] = value
