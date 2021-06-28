# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


import time
import copy
import dataclasses
import google.protobuf.json_format as parser
import asyncio
import typing
import random
import functools

from aiohttp import ClientSession
from asyncio import as_completed
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from logging import Logger, getLogger

from diem import diem_types, utils, TREASURY_ADDRESS
from diem.jsonrpc import jsonrpc_pb2 as rpc
from diem.jsonrpc.constants import (
    ACCOUNT_ROLE_PARENT_VASP,
    ACCOUNT_ROLE_CHILD_VASP,
    VM_STATUS_EXECUTED,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY,
    DEFAULT_WAIT_FOR_TRANSACTION_TIMEOUT_SECS,
    DEFAULT_WAIT_FOR_TRANSACTION_WAIT_DURATION_SECS,
    USER_AGENT_HTTP_HEADER,
)
from diem.jsonrpc.errors import (
    JsonRpcError,
    InvalidServerResponse,
    StaleResponseError,
    TransactionHashMismatchError,
    TransactionExecutionFailed,
    TransactionExpired,
    WaitForTransactionTimeout,
    AccountNotFoundError,
)
from diem.jsonrpc.state import State


@dataclasses.dataclass
class Retry:
    max_retries: int
    delay_secs: float
    exception: typing.Type[Exception]

    async def execute(self, coro):  # pyre-ignore
        tries = 0
        while tries < self.max_retries:
            tries += 1
            try:
                return await coro()
            except self.exception as e:
                if tries < self.max_retries:
                    # simplest backoff strategy: tries * delay
                    await asyncio.sleep(self.delay_secs * tries)
                else:
                    raise e


class RequestStrategy:
    """RequestStrategy base class

    It implements the simplest strategy: direct send http request
    """

    async def send_request(
        self, client: "AsyncClient", request: typing.Dict[str, typing.Any], ignore_stale_response: bool
    ) -> typing.Dict[str, typing.Any]:
        return await client._send_http_request(client._url, request, ignore_stale_response)


class RequestWithBackups(RequestStrategy):
    """RequestWithBackups implements strategies for primary-backup model.

    First we send same request to primary and one of random picked backup urls in parallel.
    Then we have 2 different strategies for how we handle responses:

    1. first success: return first completed success response.
    2. fallback: wait for primary response completed, if it failed, fallback to backup response.

    Default is first success strategy, passing fallback=True in constructor to enable fallback strategy.

    Errors cause failures:

    1. http request error
    2. http response error
    3. response body is not json
    4. StaleResponseError: this is included for making sure we always prefer to pick non-stale response.

    Initialize Client:

    ```python
    from diem import jsonrpc

    jsonrpc.AsyncClient(
        <primary-json-rpc-server-url>
        rs=jsonrpc.async_client.RequestWithBackups(backups=[<backup-json-rpc-server-url>...]),
    )
    ```
    """

    def __init__(
        self,
        backups: typing.List[str],
        fallback: bool = False,
    ) -> None:
        self._backups = backups
        self._fallback = fallback

    async def send_request(
        self, client: "AsyncClient", request: typing.Dict[str, typing.Any], ignore_stale_response: bool
    ) -> typing.Dict[str, typing.Any]:
        primary = asyncio.create_task(client._send_http_request(client._url, request, ignore_stale_response))

        backup = asyncio.create_task(
            client._send_http_request(random.choice(self._backups), request, ignore_stale_response)
        )

        if self._fallback:
            return await self._fallback_to_backup(primary, backup)
        return await self._first_success(primary, backup)

    async def _fallback_to_backup(self, primary: asyncio.Task, backup: asyncio.Task) -> typing.Dict[str, typing.Any]:
        try:
            return await primary
        except Exception:
            return await backup

    async def _first_success(self, primary: asyncio.Task, backup: asyncio.Task) -> typing.Dict[str, typing.Any]:
        futures = as_completed({primary, backup})
        first = next(futures)
        try:
            return await first
        except Exception:
            return await next(futures)


class AsyncClient:
    """Diem JSON-RPC API asyncio client

    [SPEC](https://github.com/diem/diem/blob/master/json-rpc/json-rpc-spec.md)
    """

    def __init__(
        self,
        server_url: str,
        retry: typing.Optional[Retry] = None,
        rs: typing.Optional[RequestStrategy] = None,
        logger: typing.Optional[Logger] = None,
        session_factory: typing.Callable[[], ClientSession] = ClientSession,
    ) -> None:
        self._url: str = server_url
        self._session_factory = session_factory
        self._last_known_server_state: State = State(chain_id=-1, version=-1, timestamp_usecs=-1)
        self._retry: Retry = retry or Retry(DEFAULT_MAX_RETRIES, DEFAULT_RETRY_DELAY, StaleResponseError)
        self._rs: RequestStrategy = rs or RequestStrategy()
        self._logger: Logger = logger or getLogger(__name__)

    # high level functions

    async def get_parent_vasp_account(
        self, vasp_account_address: typing.Union[diem_types.AccountAddress, str]
    ) -> rpc.Account:
        """get parent_vasp account

        accepts child/parent vasp account address, returns parent vasp account

        raise ValueError if given account address is not ChildVASP or ParentVASP account
        address
        raise AccountNotFoundError if no account found by given account address, or
        could not find the account by the parent_vasp_address found in ChildVASP account.
        """

        account = await self.must_get_account(vasp_account_address)

        if account.role.type == ACCOUNT_ROLE_PARENT_VASP:
            return account
        if account.role.type == ACCOUNT_ROLE_CHILD_VASP:
            return await self.get_parent_vasp_account(account.role.parent_vasp_address)

        hex = utils.account_address_hex(vasp_account_address)
        raise ValueError(f"given account address({hex}) is not a VASP account: {account}")

    async def get_base_url_and_compliance_key(
        self, account_address: typing.Union[diem_types.AccountAddress, str]
    ) -> typing.Tuple[str, Ed25519PublicKey]:
        """get base_url and compliance key

        ParentVASP or Designated Dealer account role has base_url and compliance key setup, which
        are used for offchain API communication.
        """
        account = await self.must_get_account(account_address)

        if account.role.compliance_key and account.role.base_url:
            key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(account.role.compliance_key))
            return (account.role.base_url, key)
        if account.role.parent_vasp_address:
            return await self.get_base_url_and_compliance_key(account.role.parent_vasp_address)

        raise ValueError(f"could not find base_url and compliance_key from account: {account}")

    async def must_get_account(self, account_address: typing.Union[diem_types.AccountAddress, str]) -> rpc.Account:
        """must_get_account raises AccountNotFoundError if account could not be found by given address"""

        account = await self.get_account(account_address)
        if account is None:
            hex = utils.account_address_hex(account_address)
            raise AccountNotFoundError(f"account not found by address: {hex}")
        return account

    async def get_account_sequence(self, account_address: typing.Union[diem_types.AccountAddress, str]) -> int:
        """get on-chain account sequence number

        Calls get_account to find on-chain account information and return it's sequence.
        Raises AccountNotFoundError if get_account returns None
        """

        account = await self.get_account(account_address)
        if account is None:
            hex = utils.account_address_hex(account_address)
            raise AccountNotFoundError(f"account not found by address: {hex}")

        return int(account.sequence_number)

    # low level functions

    def get_last_known_state(self) -> State:
        """get last known server state

        All JSON-RPC service response contains chain_id, latest ledger state version and
        ledger state timestamp usecs.
        Returns a state with all -1 values if the client never called server after initialized.
        Last known state is used for tracking server response, making sure we won't hit stale
        server.
        """

        return copy.copy(self._last_known_server_state)

    def update_last_known_state(self, chain_id: int, version: int, timestamp_usecs: int) -> None:
        """update last known server state

        Raises InvalidServerResponse if given chain_id mismatches with previous value

        Raises StaleResponseError if version or timestamp_usecs is less than previous values
        """

        curr = self._last_known_server_state
        if curr.chain_id != -1 and curr.chain_id != chain_id:
            raise InvalidServerResponse(f"last known chain id {curr.chain_id}, " f"but got {chain_id}")
        if curr.version > version:
            raise StaleResponseError(f"last known version {curr.version} > {version}")
        if curr.timestamp_usecs > timestamp_usecs:
            raise StaleResponseError(f"last known timestamp_usecs {curr.timestamp_usecs} > {timestamp_usecs}")

        self._last_known_server_state = State(
            chain_id=chain_id,
            version=version,
            timestamp_usecs=timestamp_usecs,
        )

    async def get_metadata(
        self,
        version: typing.Optional[int] = None,
    ) -> rpc.Metadata:
        """get block metadata

        See [JSON-RPC API Doc](https://github.com/diem/diem/blob/master/json-rpc/docs/method_get_metadata.md)
        """

        params = [int(version)] if version else []
        return await self.execute("get_metadata", params, _parse_obj(lambda: rpc.Metadata()))

    async def get_currencies(self) -> typing.List[rpc.CurrencyInfo]:
        """get currencies

        See [JSON-RPC API Doc](https://github.com/diem/diem/blob/master/json-rpc/docs/method_get_currencies.md)
        """

        return await self.execute("get_currencies", [], _parse_list(lambda: rpc.CurrencyInfo()))

    async def get_account(
        self, account_address: typing.Union[diem_types.AccountAddress, str]
    ) -> typing.Optional[rpc.Account]:
        """get on-chain account information

        Returns None if account not found
        See [JSON-RPC API Doc](https://github.com/diem/diem/blob/master/json-rpc/docs/method_get_account.md)
        """

        address = utils.account_address_hex(account_address)
        return await self.execute("get_account", [address], _parse_obj(lambda: rpc.Account()))

    async def get_account_transaction(
        self,
        account_address: typing.Union[diem_types.AccountAddress, str],
        sequence: int,
        include_events: typing.Optional[bool] = None,
    ) -> typing.Optional[rpc.Transaction]:
        """get on-chain account transaction by sequence number

        Returns None if transaction is not found

        See [JSON-RPC API Doc](https://github.com/diem/diem/blob/master/json-rpc/docs/method_get_account_transaction.md)
        """

        address = utils.account_address_hex(account_address)
        params = [address, int(sequence), bool(include_events)]
        return await self.execute("get_account_transaction", params, _parse_obj(lambda: rpc.Transaction()))

    async def get_account_transactions(
        self,
        account_address: typing.Union[diem_types.AccountAddress, str],
        sequence: int,
        limit: int,
        include_events: typing.Optional[bool] = None,
    ) -> typing.List[rpc.Transaction]:
        """get on-chain account transactions by start sequence number and limit size

        Returns empty list if no transactions found

        See [JSON-RPC API Doc](https://github.com/diem/diem/blob/master/json-rpc/docs/method_get_account_transactions.md)
        """

        address = utils.account_address_hex(account_address)
        params = [address, int(sequence), int(limit), bool(include_events)]
        return await self.execute("get_account_transactions", params, _parse_list(lambda: rpc.Transaction()))

    async def get_transactions(
        self,
        start_version: int,
        limit: int,
        include_events: typing.Optional[bool] = None,
    ) -> typing.List[rpc.Transaction]:
        """get transactions

        Returns empty list if no transactions found

        See [JSON-RPC API Doc](https://github.com/diem/diem/blob/master/json-rpc/docs/method_get_transactions.md)
        """

        params = [int(start_version), int(limit), bool(include_events)]
        return await self.execute("get_transactions", params, _parse_list(lambda: rpc.Transaction()))

    async def get_events(self, event_stream_key: str, start: int, limit: int) -> typing.List[rpc.Event]:
        """get events

        Returns empty list if no events found

        See [JSON-RPC API Doc](https://github.com/diem/diem/blob/master/json-rpc/docs/method_get_events.md)
        """

        params = [event_stream_key, int(start), int(limit)]
        return await self.execute("get_events", params, _parse_list(lambda: rpc.Event()))

    async def get_state_proof(self, version: int) -> rpc.StateProof:
        params = [int(version)]
        return await self.execute("get_state_proof", params, _parse_obj(lambda: rpc.StateProof()))

    async def get_account_state_with_proof(
        self,
        account_address: diem_types.AccountAddress,
        version: typing.Optional[int] = None,
        ledger_version: typing.Optional[int] = None,
    ) -> rpc.AccountStateWithProof:
        address = utils.account_address_hex(account_address)
        params = [address, version, ledger_version]
        return await self.execute(
            "get_account_state_with_proof", params, _parse_obj(lambda: rpc.AccountStateWithProof())
        )

    async def get_diem_id_domain_map(self, batch_size: int = 100) -> typing.Dict[str, str]:
        domain_map = {}
        event_index = 0
        tc_account = await self.must_get_account(utils.account_address(TREASURY_ADDRESS))
        event_stream_key = tc_account.role.diem_id_domain_events_key
        while True:
            events = await self.get_events(event_stream_key, event_index, batch_size)
            for event in events:
                if event.data.removed:
                    del domain_map[event.data.domain]
                else:
                    domain_map[event.data.domain] = event.data.address
            if len(events) < batch_size:
                break
            event_index += batch_size
        return domain_map

    async def submit(
        self,
        txn: typing.Union[diem_types.SignedTransaction, str],
    ) -> None:
        """submit signed transaction

        See [JSON-RPC API Doc](https://github.com/diem/diem/blob/master/json-rpc/docs/method_submit.md)

        This method ignores StaleResponseError and does not retry on any submit errors, because re-submit any transaction
        may get JsonRpcError `SEQUENCE_NUMBER_TOO_OLD` in multi-threads environment, for example:

        1. thread-1: submit transaction.
        2. server: receive submit transaction. The latest ledger version is X.
        3. server: receive a new state sync. The latest ledger version becomes X+1.
        4. thread-2: get_events (can be any get API).
        5. server: receive get_events. The latest ledger version is X+1.
        6. server: respond to get_events with latest ledger version == X+1.
        7. thread-2: receive get_events response.
        8. thread-2: update latest known ledger version X+1.
        9. server: respond to submit transaction with latest ledger version == X.
        10. thread-1: receive submit transaction response. Found response ledger version X < known version X+1.
        11. thread-1: triggers StaleResponseError.
        12. if we retry on StaleResponseError, the submitted transaction may end with JsonRpcError `SEQUENCE_NUMBER_TOO_OLD`
            if the following events happened.
        13. server: execute transaction, and the transaction sender account sequence number +1.
        14. thread-1: submit the transaction again.
        15. server: validate transaction sender account sequence number, and response SEQUENCE_NUMBER_TOO_OLD error.
            However, the transaction was executed successfully, thus raising SEQUENCE_NUMBER_TOO_OLD error may cause
            a re-submit with new account sequence number if client handled it improperly (without checking whether
            the transaction is executed).

        """

        if isinstance(txn, diem_types.SignedTransaction):
            return await self.submit(txn.bcs_serialize().hex())

        await self.execute_without_retry("submit", [txn], result_parser=None, ignore_stale_response=True)

    async def wait_for_transaction(
        self, txn: typing.Union[diem_types.SignedTransaction, str], timeout_secs: typing.Optional[float] = None
    ) -> rpc.Transaction:
        """wait for transaction executed

        Raises WaitForTransactionTimeout if waited timeout_secs and no expected transaction found.

        Raises TransactionExpired if server responses new block timestamp is after signed transaction
        expiration_timestamp_secs.

        Raises TransactionExecutionFailed if found transaction and it's vm_status (execution result)
        is not success.

        Raises TransactionHashMismatchError if found transaction by account address and sequence
        number, but the transaction hash does not match the transactoin hash given in parameter.
        This means the executed transaction is from another process (which submitted transaction
        with same account address and sequence).
        """

        if isinstance(txn, str):
            txn_obj = diem_types.SignedTransaction.bcs_deserialize(bytes.fromhex(txn))
            return await self.wait_for_transaction(txn_obj, timeout_secs)

        return await self.wait_for_transaction2(
            txn.raw_txn.sender,
            txn.raw_txn.sequence_number,
            txn.raw_txn.expiration_timestamp_secs,
            utils.transaction_hash(txn),
            timeout_secs,
        )

    async def wait_for_transaction2(
        self,
        address: diem_types.AccountAddress,
        seq: int,
        expiration_time_secs: int,
        txn_hash: str,
        timeout_secs: typing.Optional[float] = None,
        wait_duration_secs: typing.Optional[float] = None,
    ) -> rpc.Transaction:
        """wait for transaction executed

        Raises WaitForTransactionTimeout if waited timeout_secs and no expected transaction found.

        Raises TransactionExpired if server responses new block timestamp is after signed transaction
        expiration_timestamp_secs.

        Raises TransactionExecutionFailed if found transaction and it's vm_status (execution result)
        is not success.

        Raises TransactionHashMismatchError if found transaction by account address and sequence
        number, but the transaction hash does not match the transactoin hash given in parameter.
        This means the executed transaction is from another process (which submitted transaction
        with same account address and sequence).
        """
        max_wait = time.time() + (timeout_secs or DEFAULT_WAIT_FOR_TRANSACTION_TIMEOUT_SECS)
        while time.time() < max_wait:
            txn = await self.get_account_transaction(address, seq, True)
            if txn is not None:
                if txn.hash != txn_hash:
                    raise TransactionHashMismatchError(f"expected hash {txn_hash}, but got {txn.hash}")
                if txn.vm_status.type != VM_STATUS_EXECUTED:
                    raise TransactionExecutionFailed(f"VM status: {txn.vm_status}")
                return txn
            state = self.get_last_known_state()
            if expiration_time_secs * 1_000_000 <= state.timestamp_usecs:
                raise TransactionExpired(
                    f"latest server ledger timestamp_usecs {state.timestamp_usecs}, "
                    f"transaction expires at {expiration_time_secs}"
                )
            await asyncio.sleep(wait_duration_secs or DEFAULT_WAIT_FOR_TRANSACTION_WAIT_DURATION_SECS)

        raise WaitForTransactionTimeout()

    # pyre-ignore
    async def execute(
        self,
        method: str,
        params: typing.List[typing.Any],  # pyre-ignore
        result_parser: typing.Optional[typing.Callable] = None,  # pyre-ignore
        ignore_stale_response: typing.Optional[bool] = None,
    ):
        """execute JSON-RPC method call

        This method handles StableResponseError with retry.
        Should only be called by get methods.
        """

        return await self._retry.execute(
            functools.partial(self.execute_without_retry, method, params, result_parser, ignore_stale_response)
        )

    # pyre-ignore
    async def execute_without_retry(
        self,
        method: str,
        params: typing.List[typing.Any],  # pyre-ignore
        result_parser: typing.Optional[typing.Callable] = None,  # pyre-ignore
        ignore_stale_response: typing.Optional[bool] = None,
    ):
        """execute JSON-RPC method call without retry any error.


        Raises InvalidServerResponse if server response does not match
        [JSON-RPC SPEC 2.0](https://www.jsonrpc.org/specification), or response result can't be parsed.

        Raises StaleResponseError if ignore_stale_response is True, otherwise ignores it and continue.

        Raises JsonRpcError if server JSON-RPC response with error object.

        Raises NetworkError if send http request failed, or received server response status is not 200.
        """

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        try:
            json = await self._rs.send_request(self, request, ignore_stale_response or False)
            if "error" in json:
                err = json["error"]
                raise JsonRpcError(f"{err}")

            if "result" in json:
                if result_parser:
                    return result_parser(json["result"])
                return

            raise InvalidServerResponse(f"No error or result in response: {json}")
        except parser.ParseError as e:
            raise InvalidServerResponse(f"Parse result failed: {e}, response: {json}")

    async def _send_http_request(
        self,
        url: str,
        request: typing.Dict[str, typing.Any],
        ignore_stale_response: bool,
    ) -> typing.Dict[str, typing.Any]:
        self._logger.debug("http request body: %s", request)
        headers = {"User-Agent": USER_AGENT_HTTP_HEADER}
        async with self._session_factory() as session:
            async with session.post(url, json=request, headers=headers) as response:
                self._logger.debug("http response body: %s", response.text)
                response.raise_for_status()
                try:
                    json = await response.json()
                except ValueError as e:
                    raise InvalidServerResponse(f"Parse response as json failed: {e}, response: {response.text}")

        # check stable response before check jsonrpc error
        try:
            self.update_last_known_state(
                json.get("diem_chain_id"),
                json.get("diem_ledger_version"),
                json.get("diem_ledger_timestampusec"),
            )
        except StaleResponseError as e:
            if not ignore_stale_response:
                raise e

        return json


def _parse_obj(factory):  # pyre-ignore
    return lambda result: parser.ParseDict(result, factory(), ignore_unknown_fields=True) if result else None


def _parse_list(factory):  # pyre-ignore
    parser = _parse_obj(factory)
    return lambda result: list(map(parser, result)) if result else []
