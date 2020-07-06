# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

# pyre-strict

import requests
from typing import (
    Dict,
    Union,
    List,
    Any,
    cast,
)

from pylibra import (
    as_events,
    LibraNetwork,
    PaymentEvent,
    JSONUnknownEvent,
    ToLBRExchangeRateUpdateEvent,
    EventsType,
)

EventJSONType = Dict[str, Union[str, Dict[str, Union[str, float]]]]
TransactionJSONType = Dict[str, Union[Dict[str, str], List[EventJSONType]]]
ResponseResultJSONType = Union[
    TransactionJSONType, List[TransactionJSONType], List[EventJSONType],
]
ResponseJSONType = Dict[str, Union[int, str, ResponseResultJSONType]]


class MockResponse:
    _json_data: ResponseJSONType

    def __init__(self, json_data: ResponseResultJSONType) -> None:
        self._json_data = {"jsonrpc": "2.0", "id": 1, "result": json_data}

    def json(self) -> ResponseJSONType:
        return self._json_data

    def raise_for_status(self) -> None:
        pass

    # pyre-ignore
    def mock_post(self, url, json, timeout):
        return self


def test_as_events_blanks_cases() -> None:
    assert as_events([]) == []
    assert as_events([create_event_dict("sentpayment")], False) == []
    assert as_events([], True) == []


def test_parse_events_from_get_events() -> None:
    resp = MockResponse(create_all_types_events())
    session = requests.sessions.Session()
    session.post = resp.mock_post

    api = LibraNetwork(session=session)

    events = api.get_events("sent_events_key_hex", 0, 1)

    assert_all_types_events(events)


def test_parse_events_from_transaction_by_acc_seq() -> None:
    resp = MockResponse(create_user_type_transaction_with_events())
    session = requests.sessions.Session()
    session.post = resp.mock_post

    api = LibraNetwork(session=session)

    _, events = api.transaction_by_acc_seq("addr_hex", 0, True)

    assert_all_types_events(events)


def test_parse_events_from_transactions_by_range() -> None:
    resp = MockResponse([create_user_type_transaction_with_events()])
    session = requests.sessions.Session()
    session.post = resp.mock_post

    api = LibraNetwork(session=session)

    ret = api.transactions_by_range(start_version=0, limit=10, include_events=True)

    _, events = ret[0]
    assert_all_types_events(events)


def create_user_type_transaction_with_events() -> TransactionJSONType:
    return {
        "transaction": {"type": "user"},
        "events": create_all_types_events(),
    }


def create_all_types_events() -> List[EventJSONType]:
    return [
        create_event_dict("sentpayment"),
        create_event_dict("receivedpayment"),
        create_event_dict("unknown"),
        create_event_dict("to_lbr_exchange_rate_update", {"currency_code": "Coin1", "new_to_lbr_exchange_rate": 0.32},),
    ]


def assert_all_types_events(events: EventsType) -> None:
    assert len(events) == 4
    assert isinstance(events[0], PaymentEvent)
    assert isinstance(events[1], PaymentEvent)
    assert isinstance(events[2], JSONUnknownEvent)
    assert isinstance(events[3], ToLBRExchangeRateUpdateEvent)

    e = cast(ToLBRExchangeRateUpdateEvent, events[3])

    assert e.currency_code == "Coin1"
    assert e.new_to_lbr_exchange_rate == 0.32


def create_event_dict(type: str, attrs: Dict[str, Any] = {}) -> Dict[str, Any]:
    data = {"type": type}
    data.update(attrs)
    return {"data": data}
