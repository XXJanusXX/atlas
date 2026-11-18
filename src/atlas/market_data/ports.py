from typing import Protocol

from atlas.domain.models import Instrument, Quote


class MarketDataProvider(Protocol):
    async def list_instruments(self) -> list[Instrument]: ...

    async def get_quote(self, instrument: str) -> Quote: ...
