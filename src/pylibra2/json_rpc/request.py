import typing
from dataclasses import dataclass

import requests
from dacite import (
    Config,
    MissingValueError,
    StrictUnionMatchError,
    UnexpectedDataError,
    UnionMatchError,
    WrongTypeError,
    from_dict,
)

from .._config import (
    DEFAULT_CONNECT_TIMEOUT_SECS,
    DEFAULT_TIMEOUT_SECS,
    JSONRPC_LIBRA_CHAIN_ID,
    JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS,
    JSONRPC_LIBRA_LEDGER_VERSION,
    LIBRA_ADDRESS_LEN,
    LIBRA_EVENT_KEY_LEN,
)
from .types import (
    UNION_TYPES,
    AccountStateResponse,
    CurrencyInfo,
    CurrencyResponse,
    Event,
    JsonRpcError,
    MetadataResponse,
    Transaction,
    UserTransactionData,
    f_create_union_type,
)


class NetworkError(Exception):
    pass


class InvalidServerResponse(Exception):
    pass


def get_type_hooks() -> typing.Dict[typing.Type, typing.Callable[..., typing.Type]]:
    """ Get hooks to run before parsing a dataclass """

    def from_dict_(
        data_class: typing.Type, data: typing.Dict[str, typing.Any]
    ) -> typing.Any:
        return from_dict(data_class, data, config=Config(strict=True))

    return {_union: f_create_union_type(_union, from_dict_) for _union in UNION_TYPES}


@dataclass
class JsonRpcResponse:
    chain_id: int
    version: int
    timestamp_usecs: int
    responses: typing.List[typing.Any]


class JsonRpcBatch:
    _requests: typing.List[typing.Tuple[str, typing.List[typing.Any]]]

    def __init__(self):
        self._requests = []

    def _add_request(self, method: str, params: typing.List[typing.Any]) -> None:
        self._requests.append((method, params))

    def add_submit_request(self, signed_tx_hex: str) -> None:
        self._add_request("submit", [signed_tx_hex])

    def add_get_account_request(self, account_address_hex: str) -> None:
        if len(bytes.fromhex(account_address_hex)) != LIBRA_ADDRESS_LEN:
            raise ValueError(f"Invalid Account_address: {account_address_hex}")

        self._add_request("get_account", [account_address_hex])

    def add_get_metadata_request(self, version: typing.Optional[int] = None) -> None:
        if not version:
            version: str = "null"

        self._add_request("get_metadata", [version])

    def add_get_transactions_by_range_request(
        self, start_version: int, limit: int, include_events: bool
    ) -> None:
        self._add_request("get_transactions", [start_version, limit, include_events])

    def add_get_trasaction_by_accnt_seq_request(
        self, account_address_hex: str, sequence: int, include_events: bool
    ) -> None:
        self._add_request(
            "get_account_transaction", [account_address_hex, sequence, include_events]
        )

    def add_get_events_request(
        self, event_stream_key: str, start_sequence: int, limit: int
    ) -> None:
        if len(bytes.fromhex(event_stream_key)) != LIBRA_EVENT_KEY_LEN:
            raise ValueError(f"Invalid Event Key: {event_stream_key}")

        self._add_request("get_events", [event_stream_key, start_sequence, limit])

    def add_get_currencies_request(self) -> None:
        self._add_request("get_currencies", [])

    def get_json_rpc_request_object(
        self,
    ) -> typing.List[typing.Dict[typing.Any, typing.Any]]:

        return list(
            map(
                lambda params: {
                    "jsonrpc": "2.0",
                    "id": params[0],  # index
                    "method": params[1][0],  # method
                    "params": params[1][1],  # params
                },
                enumerate(self._requests),
            )
        )


class JsonRpcClient:
    def __init__(
        self,
        fullnode_url: str,
        session: requests.Session,
        timeout: typing.Optional[
            typing.Union[float, typing.Tuple[float, float]]
        ] = None,
    ):
        self._url = fullnode_url
        self._session = session
        if not timeout:
            self._timeout = (DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS)
        else:
            self._timeout = timeout

    def execute(self, batch: JsonRpcBatch) -> JsonRpcResponse:
        """Function to execute batch of Json RPC requests & return various response objs

        Args:
            batch (JsonRpcBatch):List of Json RPC Requests

        Returns:
            JsonRpcResponse: JsonRpcResponse obj which encapsulates version, timestamp, list of response objects.
            response objs are of various types such as AccountStateResponse, JsonRpcError etc

        """
        json_rpc_requests: typing.List[
            typing.Dict[typing.Any, typing.Any]
        ] = batch.get_json_rpc_request_object()

        try:
            response = self._session.post(
                self._url, json=json_rpc_requests, timeout=self._timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise NetworkError(
                f"Error in connecting to Full Node: {e}\nPlease retry..."
            )

        # Process the response if there is no network error
        try:
            response_json = response.json()
            json_rpc_responses: typing.List[
                typing.Dict[typing.Any, typing.Any]
            ] = response_json if type(response_json) is list else [response_json]
        except ValueError as e:
            raise InvalidServerResponse(
                f"Received invalid json from server: {e}\nFull http response: {response.text}"
            )

        return self._process_batch_responses(json_rpc_requests, json_rpc_responses)

    def _process_batch_responses(
        self,
        json_rpc_requests: typing.List[typing.Dict[typing.Any, typing.Any]],
        json_rpc_responses: typing.List[typing.Dict[typing.Any, typing.Any]],
    ) -> JsonRpcResponse:

        if len(json_rpc_requests) != len(json_rpc_responses):
            raise InvalidServerResponse(
                f"Num Responses: {len(json_rpc_responses)} != Num Requests: {len(json_rpc_requests)}"
            )

        # This dict will have mapping from id -> index of request obj
        # e.g. if 1st request has id 100, 2nd request has id 200, then we will have mapping
        #        requests_ids_map = { 100: 0,  # zero based indexing
        #                            200: 1, }
        requests_ids_map: typing.Dict[int, int] = {
            json_rpc_request["id"]: index
            for index, json_rpc_request in enumerate(json_rpc_requests)
        }

        response_objects_map: typing.Dict[int, typing.Any] = {}
        chain_id: int = 0
        version: int = 0
        timestamp_usecs: int = 0
        for json_rpc_response in json_rpc_responses:
            # sanity check the obj obtained
            self._sanity_check_json_rpc_response_object(json_rpc_response)

            response_id = json_rpc_response["id"]

            # response id should be one among the ids present in requests_ids_map
            if response_id not in requests_ids_map:
                raise InvalidServerResponse(
                    f"Response id: {response_id} is not one among Request ids: {requests_ids_map.keys()}"
                )

            # raise error if dupilicate "id" seen in response objects
            if response_id in response_objects_map:
                raise InvalidServerResponse(
                    f"Response id: {response_id} is duplicated in response obj: {json_rpc_response}"
                )

            request_index = requests_ids_map[response_id]
            request_method = json_rpc_requests[request_index]["method"]
            response_objects_map[response_id] = self._extract_result_or_error(
                json_rpc_response, request_method
            )

            chain_id = (
                json_rpc_response[JSONRPC_LIBRA_CHAIN_ID] if chain_id == 0 else chain_id
            )
            version = (
                json_rpc_response[JSONRPC_LIBRA_LEDGER_VERSION]
                if version == 0
                else version
            )
            timestamp_usecs = (
                json_rpc_response[JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS]
                if timestamp_usecs == 0
                else timestamp_usecs
            )

            # chain_id, version, timestamp_usecs should be same across all responses
            self._validate_ledger_state(
                chain_id, version, timestamp_usecs, json_rpc_response
            )

        # sorting response objects according to the request.
        # caller process the responses as per the requests added
        responses = [
            response_object
            for _, response_object in sorted(
                response_objects_map.items(), key=lambda kv: requests_ids_map[kv[0]]
            )
        ]

        return JsonRpcResponse(chain_id, version, timestamp_usecs, responses)

    def _sanity_check_json_rpc_response_object(
        self, json_rpc_response: typing.Dict[typing.Any, typing.Any]
    ) -> None:
        #  Sanity check the object received
        required_fields = [
            "id",
            JSONRPC_LIBRA_CHAIN_ID,
            JSONRPC_LIBRA_LEDGER_VERSION,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS,
        ]
        for field in required_fields:
            if field not in json_rpc_response:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nis invalid. {field} not present!"
                )

        # Validate field types
        int_fields = [
            "id",
            JSONRPC_LIBRA_CHAIN_ID,
            JSONRPC_LIBRA_LEDGER_VERSION,
            JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS,
        ]
        for field in int_fields:
            if type(json_rpc_response[field]) != int:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nis invalid. {field} type is not int!"
                )

        str_fields = ["jsonrpc"]
        for field in str_fields:
            if type(json_rpc_response[field]) != str:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nis invalid. {field} type is not str!"
                )

        # Validate field contents
        if json_rpc_response["jsonrpc"] != "2.0":
            raise InvalidServerResponse(
                f"Server response object: {json_rpc_response} \nis invalid. Expected jsonrpc version: '2.0'"
            )

    def _validate_ledger_state(
        self,
        chain_id: int,
        version: int,
        timestamp_usecs: int,
        json_rpc_response: typing.Dict[typing.Any, typing.Any],
    ):

        if chain_id != json_rpc_response[JSONRPC_LIBRA_CHAIN_ID]:
            raise InvalidServerResponse(
                f"chain_id is not same across all responses: previous_resp:{chain_id} current_resp:{json_rpc_response[JSONRPC_LIBRA_CHAIN_ID]}"
            )

        if version != json_rpc_response[JSONRPC_LIBRA_LEDGER_VERSION]:
            raise InvalidServerResponse(
                f"version is not same across all responses. previous_resp:{version} current_resp:{json_rpc_response[JSONRPC_LIBRA_LEDGER_VERSION]}"
            )

        if timestamp_usecs != json_rpc_response[JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS]:
            raise InvalidServerResponse(
                f"timestamp_usecs is not same across all responses. previous_resp:{timestamp_usecs} current_resp:{json_rpc_response[JSONRPC_LIBRA_LEDGER_TIMESTAMPUSECS]}"
            )

    def _extract_result_or_error(  # noqa [C901]
        self,
        json_rpc_response: typing.Dict[typing.Any, typing.Any],
        request_method: str,
    ) -> typing.Optional[typing.Any]:

        if "error" not in json_rpc_response and "result" not in json_rpc_response:
            raise InvalidServerResponse(
                f"Server response object: {json_rpc_response} \nhas neither error or result attribute"
            )

        if "error" in json_rpc_response:
            try:
                return JsonRpcError(**json_rpc_response["error"])
            except TypeError as e:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid error response: {e}"
                )

        # TODO (ssinghaldev) add support for other methods too. Can use some Deisgn Patterns?
        # for submit method, "result" should be None
        if request_method == "submit":
            if json_rpc_response["result"]:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. It it not None!!"
                )

        if request_method == "get_account":
            if json_rpc_response["result"]:
                try:
                    return from_dict(
                        data_class=AccountStateResponse,
                        data=json_rpc_response["result"],
                        config=Config(
                            strict=True,
                            strict_unions_match=True,
                            type_hooks=get_type_hooks(),
                        ),
                    )
                except (
                    WrongTypeError,
                    MissingValueError,
                    UnionMatchError,
                    UnexpectedDataError,
                    StrictUnionMatchError,
                ) as e:
                    raise InvalidServerResponse(
                        f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. Error: {e}"
                    )

        if request_method == "get_metadata":
            if not json_rpc_response["result"]:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. It it None!!"
                )

            try:
                return MetadataResponse(**json_rpc_response["result"])
            except TypeError as e:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. Error: {e}"
                )

        if request_method == "get_currencies":
            if not json_rpc_response["result"] or not isinstance(
                json_rpc_response["result"], typing.Sequence
            ):
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. It it None!!"
                )

            try:
                currency_response = CurrencyResponse()

                for currency_info_dict in json_rpc_response["result"]:
                    currency_response.currencies_info.append(
                        from_dict(
                            data_class=CurrencyInfo,
                            data=currency_info_dict,
                            config=Config(strict=True),
                        )
                    )

                return currency_response
            except (WrongTypeError, MissingValueError) as e:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. Error: {e}"
                )

        if request_method == "get_account_transaction":
            if json_rpc_response["result"]:
                try:
                    tx_response = from_dict(
                        data_class=Transaction,
                        data=json_rpc_response["result"],
                        config=Config(strict=True, type_hooks=get_type_hooks()),
                    )
                except (
                    WrongTypeError,
                    MissingValueError,
                    UnionMatchError,
                    UnexpectedDataError,
                ) as e:
                    raise InvalidServerResponse(
                        f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. Error: {e}"
                    )

                # Account transactions should be UserTransaction
                if not isinstance(tx_response.transaction, UserTransactionData):
                    raise InvalidServerResponse(
                        f"Server response object: {json_rpc_response} \n is not UserTransaction!"
                    )

                return tx_response

        if request_method == "get_transactions":
            if not json_rpc_response["result"] or not isinstance(
                json_rpc_response["result"], typing.Sequence
            ):
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. It it not a list!!"
                )

            try:
                transactions: typing.List[Transaction] = []
                for transaction_dict in json_rpc_response["result"]:
                    transactions.append(
                        from_dict(
                            data_class=Transaction,
                            data=transaction_dict,
                            config=Config(strict=True, type_hooks=get_type_hooks()),
                        )
                    )

                return transactions
            except (
                WrongTypeError,
                MissingValueError,
                UnionMatchError,
                UnexpectedDataError,
            ) as e:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. Error: {e}"
                )

        if request_method == "get_events":
            if not json_rpc_response["result"] or not isinstance(
                json_rpc_response["result"], typing.Sequence
            ):
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. It it not a list!!"
                )

            try:
                events: typing.List[Event] = []
                for event_dict in json_rpc_response["result"]:
                    events.append(
                        from_dict(
                            data_class=Event,
                            data=event_dict,
                            config=Config(
                                strict=True,
                                strict_unions_match=True,
                                type_hooks=get_type_hooks(),
                            ),
                        )
                    )

                return events
            except (
                WrongTypeError,
                MissingValueError,
                UnionMatchError,
                UnexpectedDataError,
                StrictUnionMatchError,
            ) as e:
                raise InvalidServerResponse(
                    f"Server response object: {json_rpc_response} \nhas invalid result response for {request_method}. Error: {e}"
                )
