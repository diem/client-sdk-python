# pyre-strict

import requests
import typing
from requests.exceptions import RequestException

from ._config import NETWORK_DEFAULT, ENDPOINT_CONFIG, DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS


class FaucetError(Exception):
    pass


class FaucetUtils:
    """Utility class for faucet service."""

    def __init__(self, network: str = NETWORK_DEFAULT) -> None:
        self._baseurl: str = ENDPOINT_CONFIG[network]["faucet"]

    def mint(
        self,
        authkey_hex: str,
        libra_amount: float,
        session: typing.Optional[requests.Session] = None,
        timeout: typing.Optional[typing.Union[float, typing.Tuple[float, float]]] = None,
    ) -> int:
        """Request faucet to send libra to destination address."""
        if len(authkey_hex) != 64:
            raise ValueError("Invalid argument for authkey")

        if libra_amount <= 0:
            raise ValueError("Invalid argument for libra_amount")

        _session = session if session else requests.Session()
        try:
            r = _session.post(
                self._baseurl,
                params={"amount": int(libra_amount * 1_000_000), "auth_key": authkey_hex},
                timeout=timeout if timeout else (DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS),
            )
            r.raise_for_status()
            if r.text:
                return int(r.text)
            return 0
        except RequestException as e:
            raise FaucetError(e)
        finally:
            if not session:
                _session.close()
