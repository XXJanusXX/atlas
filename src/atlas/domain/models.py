from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class Instrument(BaseModel):
    symbol: str
    base_currency: str
    quote_currency: str
    group: str
    minimum_units: Decimal | None = None
    unit_increment: Decimal | None = None
    price_precision: int | None = None
    is_tradeable: bool = True


class Quote(BaseModel):
    instrument: str
    bid: Decimal
    ask: Decimal
    timestamp: datetime

    def validate_market(self) -> None:
        if self.bid <= 0 or self.ask <= 0 or self.ask < self.bid:
            raise ValueError("Invalid bid/ask quote.")


class TradeProposal(BaseModel):
    instrument: str
    side: Side
    entry_reference: Decimal
    stop_loss: Decimal
    take_profit: Decimal | None = None
    rationale: str = Field(min_length=1, max_length=2000)
    strategy_id: str
    created_at: datetime
    model_advice: dict[str, object] = Field(default_factory=dict)


class RiskDecision(BaseModel):
    approved: bool
    reason_codes: list[str] = Field(default_factory=list)
    approved_units: Decimal = Decimal("0")
    max_loss_account_currency: Decimal = Decimal("0")


class PaperOrder(BaseModel):
    order_id: str
    instrument: str
    side: Side
    units: Decimal
    requested_at: datetime
    status: str = "accepted"
