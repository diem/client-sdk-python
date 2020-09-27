# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0
# pyre-strict


import time
import copy
import dataclasses
import google.protobuf.json_format as parser
import requests
import threading
import typing

from .. import libra_types, utils
from . import libra_jsonrpc_types_pb2 as rpc


DEFAULT_CONNECT_TIMEOUT_SECS: float = 5.0
DEFAULT_TIMEOUT_SECS: float = 30.0
DEFAULT_WAIT_FOR_TRANSACTION_TIMEOUT_SECS: float = 5.0
DEFAULT_WAIT_FOR_TRANSACTION_WAIT_DURATION_SECS: float = 0.2


class JsonRpcError(Exception):
    pass


class NetworkError(Exception):
    pass


class InvalidServerResponse(Exception):
    pass


class StaleResponseError(Exception):
    pass


class TransactionHashMismatchError(Exception):
    pass


class TransactionExecutionFailed(Exception):
    pass


class TransactionExpired(Exception):
    pass


class WaitForTransactionTimeout(Exception):
    pass


@dataclasses.dataclass
class State:
    chain_id: int
    version: int
    timestamp_usecs: int


@dataclasses.dataclass
class Retry:
    max_retries: int
    delay_secs: float
    exception: typing.Type[Exception]

    def execute(self, fn: typing.Callable):  # pyre-ignore
        tries = 0
        while tries < self.max_retries:
            tries += 1
            try:
                return fn()
            except self.exception as e:
                if tries < self.max_retries:
                    # simplest backoff strategy: tries * delay
                    time.sleep(self.delay_secs * tries)
                else:
                    raise e


class Client:
    """Libra JSON-RPC API client

    [SPEC](https://github.com/libra/libra/blob/master/json-rpc/json-rpc-spec.md)
    """

    def __init__(
        self,
        server_url: str,
        session: typing.Optional[requests.Session] = None,
        timeout: typing.Optional[typing.Tuple[float, float]] = None,
        retry: typing.Optional[Retry] = None,
    ) -> None:
        self._url: str = server_url
        self._session: requests.Session = session or requests.Session()
        self._timeout: typing.Tuple[float, float] = timeout or (DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS)
        self._last_known_server_state: State = State(chain_id=-1, version=-1, timestamp_usecs=-1)
        self._lock = threading.Lock()
        self._retry: Retry = retry or Retry(5, 0.2, StaleResponseError)

    def get_last_known_state(self) -> State:
        """get last known server state

        All JSON-RPC service response contains chain_id, latest ledger state version and
        ledger state timestamp usecs.
        Returns a state with all -1 values if the client never called server after initialized.
        Last known state is used for tracking server response, making sure we won't hit stale
        server.
        """

        with self._lock:
            return copy.copy(self._last_known_server_state)

    def update_last_known_state(self, chain_id: int, version: int, timestamp_usecs: int) -> None:
        with self._lock:
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

    def get_metadata(
        self,
        version: typing.Optional[int] = None,
    ) -> rpc.BlockMetadata:  # pyre-ignore
        params = [int(version)] if version else []
        return self.execute("get_metadata", params, _parse_obj(lambda: rpc.BlockMetadata()))

    def get_currencies(self) -> typing.List[rpc.CurrencyInfo]:  # pyre-ignore
        return self.execute("get_currencies", [], _parse_list(lambda: rpc.CurrencyInfo()))

    def get_account(self, account_address: typing.Union[libra_types.AccountAddress, str]) -> rpc.Account:  # pyre-ignore
        address = utils.account_address_hex(account_address)
        return self.execute("get_account", [address], _parse_obj(lambda: rpc.Account()))

    def get_account_transaction(
        self,
        account_address: typing.Union[libra_types.AccountAddress, str],
        sequence: int,
        include_events: typing.Optional[bool] = None,
    ) -> rpc.Transaction:  # pyre-ignore
        address = utils.account_address_hex(account_address)
        params = [address, int(sequence), bool(include_events)]
        return self.execute("get_account_transaction", params, _parse_obj(lambda: rpc.Transaction()))

    def get_account_transactions(
        self,
        account_address: typing.Union[libra_types.AccountAddress, str],
        sequence: int,
        limit: int,
        include_events: typing.Optional[bool] = None,
    ) -> typing.List[rpc.Transaction]:
        address = utils.account_address_hex(account_address)
        params = [address, int(sequence), int(limit), bool(include_events)]
        return self.execute("get_account_transactions", params, _parse_list(lambda: rpc.Transaction()))

    def get_transactions(
        self,
        start_version: int,
        limit: int,
        include_events: typing.Optional[bool] = None,
    ) -> typing.List[rpc.Transaction]:
        params = [int(start_version), int(limit), bool(include_events)]
        return self.execute("get_transactions", params, _parse_list(lambda: rpc.Transaction()))

    def get_events(self, event_stream_key: str, start: int, limit: int) -> typing.List[rpc.Event]:  # pyre-ignore
        params = [event_stream_key, int(start), int(limit)]
        return self.execute("get_events", params, _parse_list(lambda: rpc.Event()))

    def get_state_proof(self, version: int) -> rpc.StateProof:  # pyre-ignore
        params = [int(version)]
        return self.execute("get_state_proof", params, _parse_obj(lambda: rpc.StateProof()))

    def get_account_state_with_proof(
        self,
        account_address: libra_types.AccountAddress,
        version: typing.Optional[int] = None,
        ledger_version: typing.Optional[int] = None,
    ) -> rpc.AccountStateWithProof:  # pyre-ignore
        address = utils.account_address_hex(account_address)
        params = [address, version, ledger_version]
        return self.execute("get_account_state_with_proof", params, _parse_obj(lambda: rpc.AccountStateWithProof()))

    def submit(
        self,
        txn: typing.Union[libra_types.SignedTransaction, str],
        raise_stale_response: typing.Optional[typing.Union[bool]] = None,
    ) -> None:
        if isinstance(txn, libra_types.SignedTransaction):
            return self.submit(txn.lcs_serialize().hex())

        self.execute_without_retry("submit", [txn], result_parser=None, ignore_stale_response=not raise_stale_response)

    def wait_for_transaction(
        self, txn: typing.Union[libra_types.SignedTransaction, str], timeout_secs: typing.Optional[float] = None
    ) -> rpc.Transaction:
        if isinstance(txn, str):
            txn_obj = libra_types.SignedTransaction.lcs_deserialize(bytes.fromhex(txn))
            return self.wait_for_transaction(txn_obj, timeout_secs)

        return self.wait_for_transaction2(
            txn.raw_txn.sender,
            txn.raw_txn.sequence_number,
            txn.raw_txn.expiration_timestamp_secs,
            utils.transaction_hash(txn),
            timeout_secs,
        )

    def wait_for_transaction2(
        self,
        address: libra_types.AccountAddress,
        seq: int,
        expiration_time_secs: int,
        txn_hash: str,
        timeout_secs: typing.Optional[float] = None,
        wait_duration_secs: typing.Optional[float] = None,
    ) -> rpc.Transaction:
        max_wait = time.time() + (timeout_secs or DEFAULT_WAIT_FOR_TRANSACTION_TIMEOUT_SECS)
        while time.time() < max_wait:
            txn = self.get_account_transaction(address, seq)
            if txn is not None:
                if txn.hash != txn_hash:
                    raise TransactionHashMismatchError(f"expected hash {txn_hash}, but got {txn.hash}")
                if txn.vm_status.type != "executed":
                    raise TransactionExecutionFailed(f"VM status: {txn.vm_status}")
                return txn
            state = self.get_last_known_state()
            if expiration_time_secs * 1_000_000 <= state.timestamp_usecs:
                raise TransactionExpired(
                    f"latest server ledger timestamp_usecs {state.timestamp_usecs}, "
                    f"transaction expires at {expiration_time_secs}"
                )
            time.sleep(wait_duration_secs or DEFAULT_WAIT_FOR_TRANSACTION_WAIT_DURATION_SECS)

        raise WaitForTransactionTimeout()

    def execute(self, *args, **kwargs):  # pyre-ignore
        return self._retry.execute(lambda: self.execute_without_retry(*args, **kwargs))

    # pyre-ignore
    def execute_without_retry(
        self,
        method: str,
        params,  # pyre-ignore
        result_parser=None,  # pyre-ignore
        ignore_stale_response: typing.Optional[bool] = None,
    ):
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        try:
            response = self._session.post(self._url, json=request, timeout=self._timeout)
            response.raise_for_status()
            json = response.json()

            # check stable response before check jsonrpc error
            try:
                self.update_last_known_state(
                    json.get("libra_chain_id"),
                    json.get("libra_ledger_version"),
                    json.get("libra_ledger_timestampusec"),
                )
            except StaleResponseError as e:
                if not ignore_stale_response:
                    raise e

            if "error" in json:
                err = json["error"]
                raise JsonRpcError(f"{err}")

            if "result" in json:
                if result_parser:
                    return result_parser(json["result"])
                return

            raise InvalidServerResponse(f"No error or result in response: {response.text}")
        except requests.RequestException as e:
            raise NetworkError(f"Error in connecting to Full Node: {e}\nPlease retry...")
        except ValueError as e:
            raise InvalidServerResponse(f"Parse response as json failed: {e}, response: {response.text}")
        except parser.ParseError as e:
            raise InvalidServerResponse(f"Parse result failed: {e}, response: {response.text}")


def _parse_obj(factory):  # pyre-ignore
    return lambda result: parser.ParseDict(result, factory(), ignore_unknown_fields=True) if result else None


def _parse_list(factory):  # pyre-ignore
    parser = _parse_obj(factory)
    return lambda result: list(map(parser, result)) if result else []
