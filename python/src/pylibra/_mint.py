# pyre-strict

import requests
from requests.exceptions import RequestException

from . import NETWORK_DEFAULT, ENDPOINT_CONFIG


class FaucetError(Exception):
    pass


class FaucetUtils:
    """Utility class for faucet service."""

    def __init__(self, network: str = NETWORK_DEFAULT) -> None:
        self._baseurl: str = ENDPOINT_CONFIG[network]["faucet"]

    def mint(self, authkey_hex: str, libra_amount: float) -> int:
        """Request faucet to send libra to destination address."""
        if len(authkey_hex) != 64:
            raise ValueError("Invalid argument for authkey")

        if libra_amount <= 0:
            raise ValueError("Invalid argument for libra_amount")

        try:
            r = requests.post(self._baseurl, params={"amount": int(libra_amount * 1_000_000), "auth_key": authkey_hex})
            r.raise_for_status()
            if r.text:
                return int(r.text)
            return 0
        except RequestException as e:
            raise FaucetError(e)
