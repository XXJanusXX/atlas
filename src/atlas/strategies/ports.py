from typing import Protocol

from atlas.domain.models import Quote, TradeProposal


class Strategy(Protocol):
    strategy_id: str

    def evaluate(self, quote: Quote) -> TradeProposal | None: ...
