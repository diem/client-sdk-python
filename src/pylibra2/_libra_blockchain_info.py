from .json_rpc.types import CurrencyInfo, MetadataResponse


class LibraBlockchainMetadata:
    def __init__(self, metadata: MetadataResponse):
        self._metadata = metadata

    @property
    def version(self) -> int:
        return self._metadata.version

    @property
    def timestamp_usecs(self) -> int:
        return self._metadata.timestamp


class LibraCurrency:
    def __init__(self, currency_info: CurrencyInfo):
        self._currency_info = currency_info

    @property
    def code(self) -> str:
        return self._currency_info.code

    @property
    def fractional_part(self) -> int:
        return self._currency_info.fractional_part

    @property
    def scaling_factor(self) -> int:
        return self._currency_info.scaling_factor

    @property
    def to_lbr_exchange_rate(self) -> float:
        return self._currency_info.to_lbr_exchange_rate

    @property
    def mint_events_key(self) -> bytes:
        return bytes.fromhex(self._currency_info.mint_events_key)

    @property
    def burn_events_key(self) -> bytes:
        return bytes.fromhex(self._currency_info.burn_events_key)

    @property
    def preburn_events_key(self) -> bytes:
        return bytes.fromhex(self._currency_info.preburn_events_key)

    @property
    def cancel_burn_events_key(self) -> bytes:
        return bytes.fromhex(self._currency_info.cancel_burn_events_key)

    @property
    def exchange_rate_update_events_key(self) -> bytes:
        return bytes.fromhex(self._currency_info.exchange_rate_update_events_key)
