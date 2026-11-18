from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from atlas.domain.models import Instrument, Quote
from atlas.market_data.validation import (
    MarketDataValidationError,
    eligible_instruments,
    validate_quote,
)


def test_stale_quote_is_rejected() -> None:
    now = datetime.now(timezone.utc)
    quote = Quote(
        instrument="EUR_USD", bid=Decimal("1.1"), ask=Decimal("1.1002"),
        timestamp=now - timedelta(seconds=20),
    )
    with pytest.raises(MarketDataValidationError, match="stale"):
        validate_quote(quote, now=now)


def test_fresh_quote_is_accepted() -> None:
    now = datetime.now(timezone.utc)
    quote = Quote(
        instrument="EUR_USD", bid=Decimal("1.1"), ask=Decimal("1.1002"),
        timestamp=now,
    )
    assert validate_quote(quote, now=now) == quote


def test_universe_requires_sizing_metadata() -> None:
    complete = Instrument(
        symbol="EUR_USD", base_currency="EUR", quote_currency="USD",
        group="major", minimum_units=Decimal("1"),
        unit_increment=Decimal("1"), price_precision=5,
    )
    incomplete = Instrument(
        symbol="USD_TRY", base_currency="USD", quote_currency="TRY",
        group="exotic",
    )
    assert eligible_instruments([incomplete, complete]) == [complete]
