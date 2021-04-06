# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field, replace, asdict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import List, Optional, Any, Dict, Callable
from .app import PaymentUri, KycSample, Event, Payment
from .app.store import _match
from ... import offchain, jsonrpc
import requests, logging, random, string, json, time


@dataclass
class RestClient:
    name: str
    server_url: str
    session: requests.Session = field(default_factory=requests.Session)
    logger: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(self.name)

    def with_retry(self, retry: Retry = Retry(total=5, connect=5, backoff_factor=0.01)) -> "RestClient":
        self.session.mount(self.server_url, HTTPAdapter(max_retries=retry))
        return self

    def create_account(
        self,
        balances: Optional[Dict[str, int]] = None,
        kyc_data: Optional[str] = None,
        reject_additional_kyc_data_request: Optional[bool] = None,
    ) -> "AccountResource":
        kwargs = {
            "balances": balances,
            "kyc_data": kyc_data,
            "reject_additional_kyc_data_request": reject_additional_kyc_data_request,
        }
        account = self.create("/accounts", **{k: v for k, v in kwargs.items() if v})
        return AccountResource(client=self, id=account["id"], kyc_data=kyc_data)

    def new_soft_match_kyc_data(self) -> str:
        return self.new_kyc_data(sample="soft_match")

    def new_reject_kyc_data(self) -> str:
        return self.new_kyc_data(sample="reject")

    def new_soft_reject_kyc_data(self) -> str:
        return self.new_kyc_data(sample="soft_reject")

    def new_valid_kyc_data(self) -> str:
        return self.new_kyc_data(sample="minimum")

    def new_kyc_data(self, name: Optional[str] = None, sample: str = "minimum") -> str:
        obj = offchain.from_json(getattr(self.kyc_sample(), sample), offchain.KycDataObject)
        if not name:
            name = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return offchain.to_json(replace(obj, legal_entity_name=name))

    def kyc_sample(self) -> KycSample:
        return KycSample(**self.send("GET", "/kyc_sample").json())

    def create(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        return self.send("POST", path, json.dumps(kwargs) if kwargs else None).json()

    def get(self, path: str) -> Dict[str, Any]:
        return self.send("GET", path).json()

    def send(self, method: str, path: str, data: Optional[str] = None) -> requests.Response:
        url = "%s/%s" % (self.server_url.rstrip("/"), path.lstrip("/"))
        self.logger.debug("%s %s: %s", method, path, data)
        resp = self.session.request(
            method=method,
            url=url.lower(),
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": jsonrpc.client.USER_AGENT_HTTP_HEADER},
        )
        log_level = logging.DEBUG if resp.status_code < 300 else logging.ERROR
        self.logger.log(log_level, "%s %s: %s - %s", method, path, data, resp.status_code)
        self.logger.log(log_level, "response body: \n%s", try_json(resp.text))
        resp.raise_for_status()
        return resp


def try_json(text: str) -> str:
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            # pretty print error json stacktrace info
            return "\n".join(["%s: %s" % (k, v) for k, v in obj.items()])
        return json.dumps(obj, indent=2)
    except Exception:
        return text


@dataclass
class AccountResource:

    client: RestClient
    id: str
    kyc_data: Optional[str] = field(default=None)

    def balance(self, currency: str) -> int:
        """Get account balance for the given currency

        Calls `GET /accounts/{account_id}/balances` endpoint and only return balance of the given currency.
        Returns 0 if given currency does not exist in the returned balances.
        """

        return self.balances().get(currency, 0)

    def send_payment(self, currency: str, amount: int, payee: str) -> Payment:
        """Send amount of currency to payee

        Calls `POST /accounts/{account_id}/payments` endpoint and returns payment details.
        """

        p = self.client.create(self._resources("payment"), payee=payee, currency=currency, amount=amount)
        return Payment(**p)

    def generate_payment_uri(self, currency: Optional[str] = None, amount: Optional[int] = None) -> PaymentUri:
        """Generate payment URI

        Calls `POST /accounts/{account_id}/payment_uris` endpoint and returns payment URI string and `id`.
        """

        return PaymentUri(**self.client.create(self._resources("payment_uri"), currency=currency, amount=amount))

    def generate_account_identifier(self, hrp: str) -> str:
        """Generate an account identifier

        Calls `generate_payment_uri` to generate payment URI and then decode account identifier from it.
        """

        return self.generate_payment_uri().intent(hrp).account_id

    def events(self, start: int = 0) -> List[Event]:
        """Get account events

        Calls to `GET /accounts/{account_id}/events` endpoint and returns events list.

        Raises `requests.HTTPError`, if the endpoint is not implemented.
        """

        ret = self.client.send("GET", self._resources("event")).json()
        return [Event(**obj) for obj in ret[start:]]

    def wait_for_balance(self, currency: str, amount: int) -> None:
        """Wait for account balance of the given currency meets given `amount`

        Raises TimeoutError and AssertionError if waitted too long time (about 12 seconds,
        120 tries for every 0.1 second).
        """

        def fn() -> None:
            assert self.balance(currency) == amount

        self.wait_for(fn)

    def find_event(self, event_type: str, start_index: int = 0, **kwargs: Any) -> Optional[Event]:
        """Find a specific event by `type`, `start_index` and `data`

        When matching the event `data`, it assumes `data` is JSON encoded dictionary, and
        returns the event if the `**kwargs` is subset of the dictionary decoded from event `data` field.
        """

        events = [e for e in self.events(start_index) if e.type == event_type]
        for e in events:
            if _match(json.loads(e.data), **kwargs):
                return e

    def wait_for_event(self, event_type: str, start_index: int = 0, **kwargs: Any) -> None:
        """Wait for a specific event happened.

        Internally calls to `find_event` to decided whether the event happened.
        See `find_event` for arguments document.
        """

        def fn() -> None:
            event = self.find_event(event_type, start_index=start_index, **kwargs)
            assert event, "could not find %s event with %s" % (event_type, (start_index, kwargs))

        self.wait_for(fn)

    def wait_for(self, fn: Callable[[], None], max_tries: int = 120, delay: float = 0.1) -> None:
        """Wait for a fucntion call success

        The given `fn` argument should:

            1. Raise `AssertionError` for the case condition not meet and continue to wait.
            2. Return `None` for success (meet condition)
        """

        tries = 0
        while True:
            tries += 1
            try:
                return fn()
            except AssertionError as e:
                if tries >= max_tries:
                    raise TimeoutError("account(%s) events: %s" % (self.id, self.dump_events())) from e
                time.sleep(delay)

    def log_events(self) -> None:
        """Log account events as INFO

        Does nothing if get events API is not implemented.
        """

        events = self.dump_events()
        if events:
            self.client.logger.info("account(%s) events: %s", self.id, events)

    def dump_events(self) -> str:
        """Dump account events as JSON encoded string (well formatted, and indent=2)

        Returns empty string if get events API is not implemented.
        """

        try:
            return json.dumps(list(map(self.event_asdict, self.events())), indent=2)
        except requests.HTTPError:
            return ""

    def event_asdict(self, event: Event) -> Dict[str, Any]:
        """Returns `Event` as dictionary object.

        As we use JSON-encoded string field, this function tries to decoding all JSON-encoded
        string as dictionary for pretty print event data in log.

        First try to decode `data` as JSON-encoded object.
        If there is `kyc_data` field, try decoding it as JSON-encoded object as well (for the
        Python SDK mini-wallet application `created_account` event.
        """

        ret = asdict(event)
        try:
            ret["data"] = json.loads(event.data)
            if ret["data"].get("kyc_data"):
                ret["data"]["kyc_data"] = json.loads(ret["data"]["kyc_data"])
        except json.decoder.JSONDecodeError:
            pass
        return ret

    def info(self, *args: Any, **kwargs: Any) -> None:
        """Log info to `client.logger`"""

        self.client.logger.info(*args, **kwargs)

    def balances(self) -> Dict[str, int]:
        """returns account balances object

        should always prefer to use func `balance(currency) -> int`, which returns zero
        when currency not exist in the response.
        """

        return self.client.get(self._resources("balance"))

    def _resources(self, resource: str) -> str:
        return "/accounts/%s/%ss" % (self.id, resource)
