from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from atlas.config import AccountConfig, RiskConfig, RuntimeConfig
from atlas.domain.models import Instrument, PaperOrder, Quote, Side, TradeProposal
from atlas.execution.paper_broker import PaperBroker
from atlas.ledger.store import Ledger
from atlas.market_data.validation import (
    MarketDataValidationError,
    eligible_instruments,
    validate_quote,
)
from atlas.orchestration.session import SessionState, assert_paper_only
from atlas.reporting.metrics import profit_factor
from atlas.risk.engine import RiskEngine
from atlas.timezones import (
    get_capital_timezone,
    get_country,
    get_country_timezone,
    get_country_timezones,
    to_capital_local_time,
)


def _quote(
    *,
    bid: str = "1.1000",
    ask: str = "1.1002",
    timestamp: datetime | None = None,
) -> Quote:
    return Quote(
        instrument="EUR_USD",
        bid=Decimal(bid),
        ask=Decimal(ask),
        timestamp=timestamp or datetime(2026, 11, 18, 12, tzinfo=UTC),
    )


def _order(side: Side = Side.BUY) -> PaperOrder:
    return PaperOrder(
        order_id="paper-001",
        instrument="EUR_USD",
        side=side,
        units=Decimal("100"),
        requested_at=datetime(2026, 11, 18, 12, tzinfo=UTC),
    )


def _proposal(
    side: Side,
    *,
    entry: str = "1.1000",
    stop: str = "1.0950",
) -> TradeProposal:
    return TradeProposal(
        instrument="EUR_USD",
        side=side,
        entry_reference=Decimal(entry),
        stop_loss=Decimal(stop),
        rationale="Deterministic test proposal",
        strategy_id="test-strategy",
        created_at=datetime(2026, 11, 18, 12, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("country", "expected"),
    [
        ("uk", "Europe/London"),
        ("United States of America", "America/New_York"),
        ("uae", "Asia/Dubai"),
    ],
)
def test_country_aliases_are_case_insensitive(country: str, expected: str) -> None:
    assert str(get_country_timezone(country)) == expected


def test_country_and_capital_lookup_normalize_whitespace_and_case() -> None:
    assert get_country("  sInGaPoRe ").country_code == "SG"
    assert str(get_capital_timezone("  tOkYo ")) == "Asia/Tokyo"


def test_hong_kong_capital_alias_resolves() -> None:
    assert str(get_capital_timezone("Hong Kong")) == "Asia/Hong_Kong"


def test_country_with_single_zone_returns_one_zone() -> None:
    assert tuple(map(str, get_country_timezones("SG"))) == ("Asia/Singapore",)


def test_capital_local_conversion_preserves_instant() -> None:
    instant = datetime(2026, 1, 1, 0, tzinfo=UTC)
    local = to_capital_local_time(instant, "Singapore")
    assert local.isoformat() == "2026-01-01T08:00:00+08:00"
    assert local.astimezone(UTC) == instant


def test_invalid_bid_ask_spread_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid bid/ask"):
        _quote(bid="1.1003", ask="1.1002").validate_market()


@pytest.mark.parametrize(
    ("bid", "ask"),
    [("0", "1.0"), ("-1.0", "1.0"), ("1.0", "0.9")],
)
def test_non_positive_or_crossed_quotes_are_rejected(bid: str, ask: str) -> None:
    with pytest.raises(ValueError, match="Invalid bid/ask"):
        _quote(bid=bid, ask=ask).validate_market()


def test_quote_within_future_tolerance_is_accepted() -> None:
    now = datetime(2026, 11, 18, 12, tzinfo=UTC)
    quote = _quote(timestamp=now + timedelta(seconds=2))
    assert validate_quote(quote, now=now) is quote


def test_quote_beyond_future_tolerance_is_rejected() -> None:
    now = datetime(2026, 11, 18, 12, tzinfo=UTC)
    quote = _quote(timestamp=now + timedelta(seconds=3))
    with pytest.raises(MarketDataValidationError, match="future"):
        validate_quote(quote, now=now)


def test_naive_reference_time_is_rejected() -> None:
    quote = _quote()
    with pytest.raises(MarketDataValidationError, match="timezone-aware"):
        validate_quote(quote, now=datetime(2026, 11, 18, 12))


def test_quote_at_maximum_age_is_accepted() -> None:
    now = datetime(2026, 11, 18, 12, tzinfo=UTC)
    quote = _quote(timestamp=now - timedelta(seconds=10))
    assert validate_quote(quote, now=now) is quote


def test_instrument_eligibility_filters_non_tradeable_unknown_and_invalid_metadata() -> None:
    valid = Instrument(
        symbol="EUR_USD",
        base_currency="EUR",
        quote_currency="USD",
        group="major",
        minimum_units=Decimal("1"),
        unit_increment=Decimal("1"),
        price_precision=5,
    )
    disabled = valid.model_copy(update={"symbol": "GBP_USD", "is_tradeable": False})
    unknown_group = valid.model_copy(update={"symbol": "ABC_XYZ", "group": "other"})
    zero_minimum = valid.model_copy(update={"symbol": "ZERO", "minimum_units": Decimal("0")})
    negative_increment = valid.model_copy(
        update={"symbol": "NEG", "unit_increment": Decimal("-1")}
    )
    invalid_precision = valid.model_copy(
        update={"symbol": "PREC", "price_precision": -1}
    )
    assert eligible_instruments(
        [disabled, unknown_group, zero_minimum, negative_increment, invalid_precision, valid]
    ) == [valid]


def test_sell_market_fill_uses_bid_minus_slippage_and_records_order() -> None:
    broker = PaperBroker(Decimal("100"))
    filled, price = broker.simulate_market_fill(
        _order(Side.SELL), _quote(), Decimal("0.0001")
    )
    assert price == Decimal("1.0999")
    assert filled.status == "filled"
    assert broker.orders == [filled]


def test_fill_rejects_slippage_that_makes_price_non_positive() -> None:
    broker = PaperBroker(Decimal("100"))
    with pytest.raises(ValueError, match="must be positive"):
        broker.simulate_market_fill(_order(Side.SELL), _quote(bid="0.0001"), Decimal("0.001"))
    assert broker.orders == []


def test_fill_rejects_invalid_quote_without_recording_order() -> None:
    broker = PaperBroker(Decimal("100"))
    with pytest.raises(ValueError, match="Invalid bid/ask"):
        broker.simulate_market_fill(_order(), _quote(bid="1.2", ask="1.1"))
    assert broker.orders == []


@pytest.mark.parametrize(
    ("side", "entry", "stop", "expected"),
    [
        (Side.BUY, "0", "1.0", "INVALID_PRICE"),
        (Side.BUY, "1.1", "0", "INVALID_PRICE"),
        (Side.BUY, "1.1", "1.1", "INVALID_STOP_DIRECTION"),
        (Side.BUY, "1.1", "1.2", "INVALID_STOP_DIRECTION"),
        (Side.SELL, "1.1", "1.1", "INVALID_STOP_DIRECTION"),
        (Side.SELL, "1.1", "1.0", "INVALID_STOP_DIRECTION"),
    ],
)
def test_risk_engine_rejects_invalid_prices_and_stop_direction(
    side: Side, entry: str, stop: str, expected: str
) -> None:
    result = RiskEngine(AccountConfig(), RiskConfig()).pre_trade_check(
        _proposal(side, entry=entry, stop=stop)
    )
    assert result.approved is False
    assert result.reason_codes == [expected]


def test_valid_sell_proposal_fails_closed_until_sizing_metadata_exists() -> None:
    result = RiskEngine(AccountConfig(), RiskConfig()).pre_trade_check(
        _proposal(Side.SELL, stop="1.1050")
    )
    assert result.approved is False
    assert result.reason_codes == ["SIZING_METADATA_REQUIRED"]


def test_account_and_risk_configuration_reject_out_of_range_values() -> None:
    with pytest.raises(ValidationError):
        AccountConfig(initial_equity=Decimal("0"))
    with pytest.raises(ValidationError):
        RiskConfig(risk_per_trade_pct=Decimal("0"))
    with pytest.raises(ValidationError):
        RiskConfig(max_open_positions=0)


def test_paper_safety_boundary_rejects_non_paper_and_live_flag() -> None:
    assert_paper_only(SessionState())
    with pytest.raises(RuntimeError, match="paper-only"):
        assert_paper_only(SessionState(execution_mode="live"))
    with pytest.raises(RuntimeError, match="paper-only"):
        assert_paper_only(SessionState(live_execution_enabled=True))


def test_profit_factor_handles_zero_loss_and_signed_losses() -> None:
    assert profit_factor(Decimal("25"), 0) is None
    assert profit_factor(100.0, -25.0) == 4.0
    assert profit_factor(100.0, 25.0) == 4.0


def test_ledger_initializes_events_table_and_closes(tmp_path) -> None:
    database_path = str(tmp_path / "atlas-test.duckdb")
    ledger = Ledger(database_path)
    rows = ledger.connection.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'events' ORDER BY ordinal_position"
    ).fetchall()
    assert [row[0] for row in rows] == [
        "event_id",
        "event_type",
        "occurred_at",
        "payload",
        "previous_hash",
        "event_hash",
    ]
    ledger.close()


def test_ledger_initialization_is_idempotent(tmp_path) -> None:
    database_path = str(tmp_path / "atlas-idempotent.duckdb")
    first = Ledger(database_path)
    first.close()
    second = Ledger(database_path)
    count = second.connection.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'events'"
    ).fetchone()[0]
    assert count == 1
    second.close()


def test_runtime_config_rejects_live_execution_mode() -> None:
    RuntimeConfig(execution_mode="paper").validate_safety_boundary()
    with pytest.raises(ValueError, match="paper mode only"):
        RuntimeConfig(execution_mode="live").validate_safety_boundary()
