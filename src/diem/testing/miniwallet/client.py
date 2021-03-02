# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field, replace, asdict
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import List, Optional, Any, Dict, Callable
from .app import PaymentUri, KycSample, Event, Payment
from .app.store import _match
from ... import offchain
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
        self, balances: Optional[Dict[str, int]] = None, kyc_data: Optional[str] = None
    ) -> "AccountResource":
        account = self.create("/accounts", kyc_data=kyc_data, balances=balances)
        return AccountResource(client=self, id=account["id"], kyc_data=account["kyc_data"])

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
        self.logger.info("%s %s: %s" % (method, path, data))
        resp = self.session.request(method=method, url=url.lower(), data=data)
        self.logger.info("response status code: %s" % resp.status_code)
        self.logger.info("response body: %s" % resp.text)
        resp.raise_for_status()
        return resp


@dataclass
class AccountResource:

    client: RestClient
    id: str
    kyc_data: str

    def balance(self, currency: str) -> int:
        return self.balances().get(currency, 0)

    def send_payment(self, currency: str, amount: int, payee: str) -> Payment:
        p = self.client.create(self._resources("payment"), payee=payee, currency=currency, amount=amount)
        return Payment(**p)

    def create_payment_uri(self) -> PaymentUri:
        return PaymentUri(**self.client.create(self._resources("payment_uri")))

    def balances(self) -> Dict[str, int]:
        return self.client.get(self._resources("balance"))

    def events(self, start: int = 0) -> List[Event]:
        ret = self.client.send("GET", self._resources("event")).json()
        return [Event(**obj) for obj in ret[start:]]

    def wait_for_balance(self, currency: str, amount: int) -> None:
        def fn() -> None:
            assert self.balance(currency) == amount, "currency: %s" % currency

        self.wait_for(fn)

    def wait_for_event(self, event_type: str, start_index: int = 0, **kwargs: Any) -> None:
        def fn() -> None:
            events = [e for e in self.events(start_index) if e.type == event_type]
            for e in events:
                if _match(json.loads(e.data), **kwargs):
                    return
            assert False, "could not find %s event with %s" % (event_type, kwargs)

        self.wait_for(fn)

    def wait_for(self, fn: Callable[[], None], max_tries: int = 120, delay: float = 0.1) -> None:
        tries = 0
        while True:
            tries += 1
            try:
                return fn()
            except AssertionError as e:
                if tries >= max_tries:
                    events = json.dumps(list(map(self.event_asdict, self.events())), indent=2)
                    raise TimeoutError("%s, events: \n%s" % (e, events)) from e
                time.sleep(delay)

    def event_asdict(self, event: Event) -> Dict[str, Any]:
        ret = asdict(event)
        try:
            ret["data"] = json.loads(event.data)
            if "kyc_data" in ret["data"]:
                ret["data"]["kyc_data"] = json.loads(ret["data"]["kyc_data"])
        except json.decoder.JSONDecodeError:
            pass
        return ret

    def info(self, *args: Any, **kwargs: Any) -> None:
        self.client.logger.info(*args, **kwargs)

    def _resources(self, resource: str) -> str:
        return "/accounts/%s/%ss" % (self.id, resource)
