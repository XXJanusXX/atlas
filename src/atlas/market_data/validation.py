from datetime import datetime, timedelta, timezone

from atlas.domain.models import Instrument, Quote


class MarketDataValidationError(ValueError):
    """Raised when market data is unsafe for downstream use."""


def validate_quote(
    quote: Quote,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(seconds=10),
    future_tolerance: timedelta = timedelta(seconds=2),
) -> Quote:
    quote.validate_market()
    current = now or datetime.now(timezone.utc)
    if quote.timestamp.tzinfo is None or current.tzinfo is None:
        raise MarketDataValidationError("Quote and reference timestamps must be timezone-aware.")
    age = current - quote.timestamp
    if age < -future_tolerance:
        raise MarketDataValidationError("Quote timestamp is unexpectedly in the future.")
    if age > max_age:
        raise MarketDataValidationError("Quote is stale.")
    return quote


def eligible_instruments(instruments: list[Instrument]) -> list[Instrument]:
    """Return instruments with enough metadata for safe paper sizing."""
    eligible: list[Instrument] = []
    for instrument in instruments:
        if not instrument.is_tradeable:
            continue
        if instrument.group not in {"major", "minor", "exotic"}:
            continue
        if instrument.minimum_units is None or instrument.unit_increment is None:
            continue
        if instrument.minimum_units <= 0 or instrument.unit_increment <= 0:
            continue
        if instrument.price_precision is None or instrument.price_precision < 0:
            continue
        eligible.append(instrument)
    return sorted(eligible, key=lambda item: (item.group, item.symbol))
