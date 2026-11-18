from datetime import datetime, UTC
from decimal import Decimal

import pytest

from atlas.domain.models import PaperOrder, Quote, Side
from atlas.execution.paper_broker import PaperBroker


NOW = datetime(2026, 11, 18, 12, tzinfo=UTC)


def _order(
    order_id: str, side: Side, units: str, instrument: str = "EUR_USD"
) -> PaperOrder:
    return PaperOrder(
        order_id=order_id,
        instrument=instrument,
        side=side,
        units=Decimal(units),
        requested_at=NOW,
    )


def _quote(
    bid: str = "1.1000", ask: str = "1.1002", instrument: str = "EUR_USD"
) -> Quote:
    return Quote(
        instrument=instrument,
        bid=Decimal(bid),
        ask=Decimal(ask),
        timestamp=NOW,
    )


def test_buy_debits_cash_and_creates_position() -> None:
    broker = PaperBroker(Decimal("100"))
    filled, price = broker.execute_market_order(_order("buy-1", Side.BUY, "50"), _quote())

    assert filled.status == "filled"
    assert price == Decimal("1.1002")
    assert broker.cash == Decimal("44.9900")
    position = broker.portfolio.positions["EUR_USD"]
    assert position.units == Decimal("50")
    assert position.average_entry_price == price


def test_weighted_average_entry_price_is_correct() -> None:
    broker = PaperBroker(Decimal("200"))
    broker.execute_market_order(_order("buy-1", Side.BUY, "50"), _quote())
    broker.execute_market_order(
        _order("buy-2", Side.BUY, "50"), _quote("1.2000", "1.2002")
    )

    position = broker.portfolio.positions["EUR_USD"]
    assert position.units == Decimal("100")
    assert position.average_entry_price == Decimal("1.1502")


def test_sell_realizes_pnl_and_deducts_fee() -> None:
    broker = PaperBroker(Decimal("100"))
    broker.execute_market_order(_order("buy-1", Side.BUY, "50"), _quote())
    broker.execute_market_order(
        _order("sell-1", Side.SELL, "50"),
        _quote("1.1100", "1.1102"),
        fee=Decimal("0.10"),
    )

    assert "EUR_USD" not in broker.portfolio.positions
    assert broker.cash == Decimal("100.3900")
    assert broker.portfolio.realized_pnl == Decimal("0.3900")
    assert broker.portfolio.fees_paid == Decimal("0.10")


def test_partial_sell_preserves_remaining_units_and_average_cost() -> None:
    broker = PaperBroker(Decimal("100"))
    broker.execute_market_order(_order("buy-1", Side.BUY, "50"), _quote())
    broker.execute_market_order(
        _order("sell-1", Side.SELL, "20"), _quote("1.1100", "1.1102")
    )

    position = broker.portfolio.positions["EUR_USD"]
    assert position.units == Decimal("30")
    assert position.average_entry_price == Decimal("1.1002")
    assert broker.portfolio.realized_pnl == Decimal("0.1960")


def test_equity_and_unrealized_pnl_use_liquidation_bid() -> None:
    broker = PaperBroker(Decimal("100"))
    broker.execute_market_order(_order("buy-1", Side.BUY, "50"), _quote())
    valuation = _quote("1.1050", "1.1052")

    assert broker.portfolio.unrealized_pnl({"EUR_USD": valuation}) == Decimal("0.2400")
    assert broker.portfolio.equity({"EUR_USD": valuation}) == Decimal("100.2400")


def test_insufficient_cash_rejects_order_without_mutating_state() -> None:
    broker = PaperBroker(Decimal("10"))
    with pytest.raises(ValueError, match="Insufficient cash"):
        broker.execute_market_order(_order("buy-1", Side.BUY, "100"), _quote())

    assert broker.cash == Decimal("10")
    assert broker.portfolio.positions == {}
    assert broker.orders == []


def test_sell_cannot_open_or_increase_a_short_position() -> None:
    broker = PaperBroker(Decimal("100"))
    with pytest.raises(ValueError, match="available long position"):
        broker.execute_market_order(_order("sell-1", Side.SELL, "1"), _quote())

    assert broker.cash == Decimal("100")
    assert broker.orders == []


def test_non_account_quote_currency_is_rejected() -> None:
    broker = PaperBroker(Decimal("100"))
    order = _order("buy-1", Side.BUY, "10", "EUR_GBP")
    with pytest.raises(ValueError, match="quote currency"):
        broker.execute_market_order(order, _quote(instrument="EUR_GBP"))

    assert broker.cash == Decimal("100")
    assert broker.orders == []


def test_missing_valuation_quote_is_rejected() -> None:
    broker = PaperBroker(Decimal("100"))
    broker.execute_market_order(_order("buy-1", Side.BUY, "10"), _quote())

    with pytest.raises(ValueError, match="Missing valuation quote"):
        broker.portfolio.equity({})


@pytest.mark.parametrize(
    ("units", "slippage", "fee"),
    [
        ("0", "0", "0"),
        ("1", "-0.0001", "0"),
        ("1", "0", "-0.01"),
    ],
)
def test_invalid_order_economics_are_rejected(
    units: str, slippage: str, fee: str
) -> None:
    broker = PaperBroker(Decimal("100"))
    with pytest.raises(ValueError):
        broker.execute_market_order(
            _order("invalid", Side.BUY, units),
            _quote(),
            slippage=Decimal(slippage),
            fee=Decimal(fee),
        )
    assert broker.orders == []
    assert broker.cash == Decimal("100")


def test_duplicate_order_id_is_rejected() -> None:
    broker = PaperBroker(Decimal("100"))
    order = _order("same-id", Side.BUY, "10")
    broker.execute_market_order(order, _quote())

    with pytest.raises(ValueError, match="Duplicate"):
        broker.execute_market_order(order, _quote())

    assert len(broker.orders) == 1


def test_entry_fee_is_included_in_average_cost_and_realized_pnl() -> None:
    broker = PaperBroker(Decimal("100"))
    broker.execute_market_order(
        _order("buy-1", Side.BUY, "50"), _quote(), fee=Decimal("0.10")
    )
    position = broker.portfolio.positions["EUR_USD"]
    assert position.average_entry_price == Decimal("1.1022")

    broker.execute_market_order(
        _order("sell-1", Side.SELL, "50"), _quote("1.1100", "1.1102")
    )
    assert broker.portfolio.realized_pnl == Decimal("0.3900")


def test_order_rejects_quote_for_different_instrument() -> None:
    broker = PaperBroker(Decimal("100"))
    with pytest.raises(ValueError, match="Quote instrument"):
        broker.execute_market_order(
            _order("buy-1", Side.BUY, "10", "EUR_USD"),
            _quote(instrument="GBP_USD"),
        )

    assert broker.cash == Decimal("100")
    assert broker.orders == []


def test_sell_fee_cannot_exceed_sale_proceeds() -> None:
    broker = PaperBroker(Decimal("100"))
    broker.execute_market_order(_order("buy-1", Side.BUY, "10"), _quote())

    with pytest.raises(ValueError, match="fee cannot exceed"):
        broker.execute_market_order(
            _order("sell-1", Side.SELL, "10"),
            _quote(),
            fee=Decimal("20"),
        )

    assert broker.cash == Decimal("88.9980")
    assert broker.portfolio.positions["EUR_USD"].units == Decimal("10")
    assert len(broker.orders) == 1
