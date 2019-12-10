import requests
from requests.exceptions import RequestException

TESTNET_FAUCET = "faucet.testnet.libra.org"


class FaucetError(Exception):
    pass


class FaucetUtils:
    """Utility class for faucet service."""

    def __init__(self, server=TESTNET_FAUCET):
        self._baseurl = "http://" + server

    def mint(self, address_hex: str, libra_amnount: float) -> int:
        """Request fauce to send libra to destination address."""
        try:
            r = requests.post(self._baseurl, params={"amount": int(libra_amnount * 1_000_000), "address": address_hex})
            r.raise_for_status()
            if r.text:
                return int(r.text)
            return 0
        except RequestException as e:
            raise FaucetError(e)
