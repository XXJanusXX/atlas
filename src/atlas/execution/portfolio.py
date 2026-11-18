from dataclasses import dataclass
from decimal import Decimal

from atlas.domain.models import PaperOrder, Quote, Side


@dataclass(frozen=True)
class Position:
    """A long spot position denominated in the instrument's base currency."""

    instrument: str
    units: Decimal
    average_entry_price: Decimal


class Portfolio:
    """Cash-only spot portfolio; all positions must be quoted in account currency.

    This deliberately excludes leverage, short selling, margin and cross-currency
    valuation. Unsupported instruments are rejected instead of approximated.
    """

    def __init__(self, initial_cash: Decimal, account_currency: str = "USD") -> None:
        if initial_cash <= 0:
            raise ValueError("Initial cash must be positive.")
        currency = account_currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("Account currency must be a three-letter code.")
        self.initial_cash = initial_cash
        self.account_currency = currency
        self.cash = initial_cash
        self.positions: dict[str, Position] = {}
        self.realized_pnl = Decimal("0")
        self.fees_paid = Decimal("0")

    def apply_fill(
        self, order: PaperOrder, fill_price: Decimal, fee: Decimal = Decimal("0")
    ) -> Position | None:
        if order.status not in {"accepted", "filled"}:
            raise ValueError("Only accepted paper orders can be filled.")
        if order.units <= 0:
            raise ValueError("Order units must be positive.")
        if fill_price <= 0:
            raise ValueError("Fill price must be positive.")
        if fee < 0:
            raise ValueError("Fee cannot be negative.")

        _, quote_currency = self._split_instrument(order.instrument)
        if quote_currency != self.account_currency:
            raise ValueError(
                "Instrument quote currency must match the portfolio account currency."
            )

        notional = order.units * fill_price
        existing = self.positions.get(order.instrument)

        if order.side == Side.BUY:
            total_cost = notional + fee
            if total_cost > self.cash:
                raise ValueError("Insufficient cash for paper purchase.")
            previous_units = existing.units if existing else Decimal("0")
            previous_cost = (
                existing.units * existing.average_entry_price if existing else Decimal("0")
            )
            new_units = previous_units + order.units
            average_price = (previous_cost + notional + fee) / new_units
            position = Position(order.instrument, new_units, average_price)
            self.positions[order.instrument] = position
            self.cash -= total_cost
        else:
            if fee > notional:
                raise ValueError("Sell fee cannot exceed sale proceeds.")
            if existing is None or order.units > existing.units:
                raise ValueError("Paper sell exceeds the available long position.")
            self.cash += notional - fee
            self.realized_pnl += (
                (fill_price - existing.average_entry_price) * order.units - fee
            )
            remaining = existing.units - order.units
            if remaining == 0:
                self.positions.pop(order.instrument)
                position = None
            else:
                position = Position(
                    order.instrument, remaining, existing.average_entry_price
                )
                self.positions[order.instrument] = position

        self.fees_paid += fee
        return position

    def unrealized_pnl(self, quotes: dict[str, Quote]) -> Decimal:
        total = Decimal("0")
        for symbol, position in self.positions.items():
            quote = quotes.get(symbol)
            if quote is None:
                raise ValueError(f"Missing valuation quote for open position: {symbol}.")
            quote.validate_market()
            if quote.instrument != symbol:
                raise ValueError(f"Valuation quote instrument mismatch: {symbol}.")
            total += (quote.bid - position.average_entry_price) * position.units
        return total

    def equity(self, quotes: dict[str, Quote]) -> Decimal:
        market_value = Decimal("0")
        for symbol, position in self.positions.items():
            quote = quotes.get(symbol)
            if quote is None:
                raise ValueError(f"Missing valuation quote for open position: {symbol}.")
            quote.validate_market()
            if quote.instrument != symbol:
                raise ValueError(f"Valuation quote instrument mismatch: {symbol}.")
            market_value += position.units * quote.bid
        return self.cash + market_value

    @staticmethod
    def _split_instrument(instrument: str) -> tuple[str, str]:
        parts = instrument.upper().split("_")
        if len(parts) != 2 or any(len(part) != 3 or not part.isalpha() for part in parts):
            raise ValueError("Instrument must use BASE_QUOTE three-letter currency notation.")
        return parts[0], parts[1]
