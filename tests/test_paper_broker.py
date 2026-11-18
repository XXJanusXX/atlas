from datetime import UTC, datetime
from decimal import Decimal

from atlas.domain.models import PaperOrder, Quote, Side
from atlas.execution.paper_broker import PaperBroker


def test_buy_market_fill_uses_ask_plus_slippage() -> None:
    broker = PaperBroker(Decimal("100"))
    order = PaperOrder(
        order_id="test-1", instrument="EUR_USD", side=Side.BUY,
        units=Decimal("100"), requested_at=datetime.now(UTC),
    )
    quote = Quote(
        instrument="EUR_USD", bid=Decimal("1.1000"), ask=Decimal("1.1002"),
        timestamp=datetime.now(UTC),
    )
    _, fill = broker.simulate_market_fill(order, quote, Decimal("0.0001"))
    assert fill == Decimal("1.1003")
