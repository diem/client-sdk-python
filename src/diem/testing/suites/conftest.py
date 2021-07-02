# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


from diem import identifier, offchain, jws, utils
from diem.jsonrpc import AsyncClient
from diem.testing import LocalAccount, XUS, create_client
from diem.testing.miniwallet import RestClient, AppConfig, AccountResource, ServerConfig, App, Transaction
from diem.testing.miniwallet.app import PENDING_INBOUND_ACCOUNT_ID
from .envs import (
    target_url,
    is_self_check,
    dmw_stub_server,
    dmw_stub_diem_account_config,
    dmw_stub_diem_account_hrp,
)
from typing import Optional, Tuple, Dict, List, Any, Generator, Callable, AsyncGenerator, Awaitable
from dataclasses import asdict
import pytest, json, uuid, time, warnings, asyncio
import secrets


@pytest.fixture(scope="package")
def event_loop() -> Generator[asyncio.events.AbstractEventLoop, None, None]:
    """Create a generator to yield an event_loop instance with graceful shutdown

    The logic is same with `asyncio.run`, except `yield` an event loop instance
    as pytest fixture.
    """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        utils.shutdown_event_loop(loop)


@pytest.fixture(scope="package")
async def target_client(diem_client: AsyncClient) -> AsyncGenerator[RestClient, None]:
    if is_self_check():
        conf = AppConfig(name="target-wallet", diem_id_domain=generate_diem_id_domain("target"))
        print("self-checking, launch target app with config %s" % conf)
        _, runner = await conf.start(diem_client)
        try:
            yield conf.create_client()
        finally:
            await runner.cleanup()
    else:
        print("target wallet server url: %s" % target_url())
        yield RestClient(name="target-wallet-client", server_url=target_url(), events_api_is_optional=True)


@pytest.fixture(scope="package")
async def diem_client() -> AsyncGenerator[AsyncClient, None]:
    async with create_client() as client:
        print("Diem JSON-RPC URL: %s" % client._url)
        yield client


@pytest.fixture(scope="package")
def stub_config(start_stub_wallet: Tuple[AppConfig, App]) -> AppConfig:
    return start_stub_wallet[0]


@pytest.fixture(scope="package")
def stub_wallet_app(start_stub_wallet: Tuple[AppConfig, App]) -> App:
    return start_stub_wallet[1]


@pytest.fixture(scope="package")
async def start_stub_wallet(diem_client: AsyncClient) -> AsyncGenerator[Tuple[AppConfig, App], None]:
    domain = generate_diem_id_domain("stub")
    conf = AppConfig(name="stub-wallet", server_conf=ServerConfig(**dmw_stub_server()), diem_id_domain=domain)
    account_conf = dmw_stub_diem_account_config()
    if account_conf:
        print("loads stub account config: %s" % account_conf)
        conf.account_config = json.loads(account_conf)
    hrp = dmw_stub_diem_account_hrp()
    if hrp:
        conf.account_config["hrp"] = hrp
    print("Start stub app with config %s" % conf)
    app, runner = await conf.start(diem_client)
    try:
        yield (conf, app)
    finally:
        await runner.cleanup()


@pytest.fixture(autouse=True)
async def log_stub_account_info(stub_config: AppConfig, diem_client: AsyncClient) -> AsyncGenerator[None, None]:
    yield
    stub_config.logger.info("=== stub wallet ParentVASP account info ===")
    data = await diem_client.get_account(stub_config.account.account_address)
    stub_config.logger.info(data)

    stub_config.logger.info("=== stub wallet ChildVASP accounts info ===")
    for i, child in enumerate(stub_config.child_accounts):
        data = await diem_client.get_account(child.account_address)
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
    return XUS


@pytest.fixture
async def travel_rule_threshold(diem_client: AsyncClient) -> int:
    # todo: convert the limit base on currency
    metadata = await diem_client.get_metadata()
    return metadata.dual_attestation_limit


@pytest.fixture
def stub_wallet_pending_income_account(stub_client: RestClient) -> AccountResource:
    """MiniWallet stub saves the payment without account information (subaddress / reference id)
    into a pending income account before processing it.
    """

    return AccountResource(id=PENDING_INBOUND_ACCOUNT_ID, client=stub_client)


@pytest.fixture(autouse=True)
async def log_stub_wallet_pending_income_account(
    stub_wallet_pending_income_account: AccountResource,
) -> AsyncGenerator[None, None]:
    yield
    await stub_wallet_pending_income_account.log_events()


@pytest.fixture
async def stub_account_diem_id_domains(stub_config: AppConfig, diem_client: AsyncClient) -> List[str]:
    account = await diem_client.get_account(stub_config.account.account_address)
    return [] if account is None else list(account.role.diem_id_domains)


@pytest.fixture
async def target_account_diem_id_domains(target_client: RestClient, diem_client: AsyncClient, hrp: str) -> List[str]:
    account_identifier = await target_client.random_account_identifier()
    account_address, _ = identifier.decode_account(account_identifier, hrp)
    account = await diem_client.get_parent_vasp_account(account_address)
    return list(account.role.diem_id_domains)


async def send_request_json(
    diem_client: AsyncClient,
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
    base_url, public_key = await diem_client.get_base_url_and_compliance_key(account_address)
    if request_body is None:
        request_body = jws.encode(request_json, sender_account.compliance_key.sign)

    url = f"{base_url.rstrip('/')}/v2/command"
    async with diem_client._session.post(url, data=request_body, headers=headers) as resp:
        cmd_resp_obj = offchain.jws.deserialize(await resp.read(), offchain.CommandResponseObject, public_key.verify)
        return (resp.status, cmd_resp_obj)


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


async def wait_for(fn: Callable[[], Awaitable[None]], max_tries: int = 60, delay: float = 0.1) -> None:
    """Wait for a function call success

    The given `fn` argument should:

        1. Raise `AssertionError` for the case condition not meet and continue to wait.
        2. Return `None` for success (meet condition)
    """

    await utils.with_retry(fn, max_tries, delay, AssertionError)


async def wait_for_balance(account: AccountResource, currency: str, amount: int) -> None:
    """Wait for account balance of the given currency meets given `amount`"""

    async def match_balance() -> None:
        balance = await account.balance(currency)
        assert balance == amount

    await wait_for(match_balance)


async def wait_for_event(account: AccountResource, event_type: str, start_index: int = 0, **kwargs: Any) -> None:
    """Wait for a specific event happened.

    Internally calls to `AccountResource#find_event` to decided whether the event happened.
    See `AccountResource#find_event` for arguments document.
    """

    async def match_event() -> None:
        event = await account.find_event(event_type, start_index=start_index, **kwargs)
        assert event, "could not find %s event with %s" % (event_type, (start_index, kwargs))

    await wait_for(match_event)


async def wait_for_payment_transaction_complete(account: AccountResource, payment_id: str) -> None:
    # MiniWallet stub generates `updated_transaction` event when transaction is completed on-chain
    # Payment id is same with Transaction id.
    await wait_for_event(account, "updated_transaction", status=Transaction.Status.completed, id=payment_id)


def generate_diem_id_domain(prefix: str) -> str:
    return prefix + secrets.token_hex(8)
