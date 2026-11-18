from decimal import Decimal

from atlas.domain.models import PaperOrder, Quote, Side


class PaperBroker:
    """Internal simulator; performs no network calls and has no live broker connection."""

    def __init__(self, initial_equity: Decimal) -> None:
        self.cash = initial_equity
        self.orders: list[PaperOrder] = []

    def simulate_market_fill(
        self, order: PaperOrder, quote: Quote, slippage: Decimal = Decimal("0")
    ) -> tuple[PaperOrder, Decimal]:
        quote.validate_market()
        if order.side == Side.BUY:
            fill_price = quote.ask + slippage
        else:
            fill_price = quote.bid - slippage
        if fill_price <= 0:
            raise ValueError("Simulated fill price must be positive.")
        filled = order.model_copy(update={"status": "filled"})
        self.orders.append(filled)
        return filled, fill_price
