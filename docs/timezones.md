# Country and Capital Timezones

ATLAS uses IANA timezone identifiers through Python's standard-library `zoneinfo`.
This avoids fixed-offset errors and applies the timezone database's daylight-saving
rules for the relevant date.

## Resolution policy

1. Country lookup accepts an ISO-3166 alpha-2 code or a registered country name.
2. The country's capital timezone is its canonical/default local timezone.
3. Countries spanning multiple zones expose a list with the capital timezone first.
4. Capital lookup resolves a registered national capital to its timezone.
5. Unknown countries, capitals and timezone identifiers fail explicitly; there is no
   silent fallback to the host machine timezone.
6. Persist event, quote, candle and execution timestamps as timezone-aware UTC.
   Convert to local time only for display, scheduling and market-session calculations.

## Initial coverage

The registry starts with 35 FX-relevant economies and jurisdictions, including
multi-zone coverage for Australia, Brazil, Canada, Indonesia, Mexico, New Zealand,
Russia, Spain and the United States. The registry is intentionally explicit and
reviewable; it is not represented as a complete global gazetteer.

## Example

```python
from datetime import UTC, datetime

from atlas.timezones import get_country_timezones, to_country_local_time

now = datetime.now(UTC)
new_york_time = to_country_local_time(now, "US")
indonesia_zones = get_country_timezones("ID")
```

## Forex session design

Market-session schedules should be stored as local wall-clock rules plus an IANA
timezone (for example, London / `Europe/London`), then evaluated against UTC.
Do not hard-code session UTC offsets: London and New York change offsets on different
dates during daylight-saving transitions. Country-capital time is a default reference,
not a substitute for a specific exchange, broker server or liquidity-provider timezone.
