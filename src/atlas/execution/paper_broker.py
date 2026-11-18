from decimal import Decimal

from atlas.domain.models import PaperOrder, Quote, Side
from atlas.execution.portfolio import Portfolio


class PaperBroker:
    """Internal simulator; performs no network calls and has no live broker connection."""

    def __init__(
        self, initial_equity: Decimal, account_currency: str = "USD"
    ) -> None:
        self.portfolio = Portfolio(initial_equity, account_currency)
        self.orders: list[PaperOrder] = []

    @property
    def cash(self) -> Decimal:
        """Available account-currency cash after purchases, sales and fees."""
        return self.portfolio.cash

    def _calculate_fill(
        self, order: PaperOrder, quote: Quote, slippage: Decimal
    ) -> tuple[PaperOrder, Decimal]:
        quote.validate_market()
        if quote.instrument != order.instrument:
            raise ValueError("Quote instrument must match the paper order instrument.")
        if slippage < 0:
            raise ValueError("Slippage cannot be negative.")
        if order.units <= 0:
            raise ValueError("Order units must be positive.")
        if order.side == Side.BUY:
            fill_price = quote.ask + slippage
        else:
            fill_price = quote.bid - slippage
        if fill_price <= 0:
            raise ValueError("Simulated fill price must be positive.")
        return order.model_copy(update={"status": "filled"}), fill_price

    def simulate_market_fill(
        self, order: PaperOrder, quote: Quote, slippage: Decimal = Decimal("0")
    ) -> tuple[PaperOrder, Decimal]:
        """Calculate and record a simulated fill without changing portfolio balances."""
        filled, fill_price = self._calculate_fill(order, quote, slippage)
        self.orders.append(filled)
        return filled, fill_price

    def execute_market_order(
        self,
        order: PaperOrder,
        quote: Quote,
        slippage: Decimal = Decimal("0"),
        fee: Decimal = Decimal("0"),
    ) -> tuple[PaperOrder, Decimal]:
        """Execute a paper fill and atomically apply its cash/position accounting."""
        if any(existing.order_id == order.order_id for existing in self.orders):
            raise ValueError("Duplicate paper order id.")
        filled, fill_price = self._calculate_fill(order, quote, slippage)
        self.portfolio.apply_fill(filled, fill_price, fee)
        self.orders.append(filled)
        return filled, fill_price
