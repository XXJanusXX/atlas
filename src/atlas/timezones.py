"""Country, capital and IANA timezone resolution.

All persisted timestamps should remain timezone-aware UTC. Convert to local time
only at presentation, scheduling and market-session boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True, slots=True)
class CountryTimezone:
    country_code: str
    country_name: str
    capital: str
    capital_timezone: str
    timezones: tuple[str, ...]


# Curated initial coverage for major FX economies and common trading jurisdictions.
# Multi-zone countries list their capital zone first, followed by additional zones.
_COUNTRIES: tuple[CountryTimezone, ...] = (
    CountryTimezone(
        "AE", "United Arab Emirates", "Abu Dhabi", "Asia/Dubai", ("Asia/Dubai",)
    ),
    CountryTimezone(
        "AU",
        "Australia",
        "Canberra",
        "Australia/Sydney",
        (
            "Australia/Sydney",
            "Australia/Melbourne",
            "Australia/Brisbane",
            "Australia/Adelaide",
            "Australia/Perth",
            "Australia/Darwin",
            "Australia/Hobart",
        ),
    ),
    CountryTimezone(
        "BR",
        "Brazil",
        "Brasilia",
        "America/Sao_Paulo",
        (
            "America/Sao_Paulo",
            "America/Manaus",
            "America/Rio_Branco",
            "America/Noronha",
        ),
    ),
    CountryTimezone(
        "CA",
        "Canada",
        "Ottawa",
        "America/Toronto",
        (
            "America/Toronto",
            "America/Vancouver",
            "America/Edmonton",
            "America/Winnipeg",
            "America/Halifax",
            "America/St_Johns",
        ),
    ),
    CountryTimezone(
        "CH", "Switzerland", "Bern", "Europe/Zurich", ("Europe/Zurich",)
    ),
    CountryTimezone("CN", "China", "Beijing", "Asia/Shanghai", ("Asia/Shanghai",)),
    CountryTimezone("CZ", "Czechia", "Prague", "Europe/Prague", ("Europe/Prague",)),
    CountryTimezone("DE", "Germany", "Berlin", "Europe/Berlin", ("Europe/Berlin",)),
    CountryTimezone(
        "DK", "Denmark", "Copenhagen", "Europe/Copenhagen", ("Europe/Copenhagen",)
    ),
    CountryTimezone("EG", "Egypt", "Cairo", "Africa/Cairo", ("Africa/Cairo",)),
    CountryTimezone(
        "ES", "Spain", "Madrid", "Europe/Madrid", ("Europe/Madrid", "Atlantic/Canary")
    ),
    CountryTimezone("FR", "France", "Paris", "Europe/Paris", ("Europe/Paris",)),
    CountryTimezone(
        "GB", "United Kingdom", "London", "Europe/London", ("Europe/London",)
    ),
    CountryTimezone(
        "HK", "Hong Kong", "Hong Kong", "Asia/Hong_Kong", ("Asia/Hong_Kong",)
    ),
    CountryTimezone(
        "HU", "Hungary", "Budapest", "Europe/Budapest", ("Europe/Budapest",)
    ),
    CountryTimezone(
        "ID",
        "Indonesia",
        "Jakarta",
        "Asia/Jakarta",
        ("Asia/Jakarta", "Asia/Makassar", "Asia/Jayapura"),
    ),
    CountryTimezone(
        "IL", "Israel", "Jerusalem", "Asia/Jerusalem", ("Asia/Jerusalem",)
    ),
    CountryTimezone("IN", "India", "New Delhi", "Asia/Kolkata", ("Asia/Kolkata",)),
    CountryTimezone("JP", "Japan", "Tokyo", "Asia/Tokyo", ("Asia/Tokyo",)),
    CountryTimezone(
        "KR", "South Korea", "Seoul", "Asia/Seoul", ("Asia/Seoul",)
    ),
    CountryTimezone(
        "MX",
        "Mexico",
        "Mexico City",
        "America/Mexico_City",
        (
            "America/Mexico_City",
            "America/Tijuana",
            "America/Chihuahua",
            "America/Cancun",
        ),
    ),
    CountryTimezone(
        "MY", "Malaysia", "Kuala Lumpur", "Asia/Kuala_Lumpur", ("Asia/Kuala_Lumpur",)
    ),
    CountryTimezone("NO", "Norway", "Oslo", "Europe/Oslo", ("Europe/Oslo",)),
    CountryTimezone(
        "NZ",
        "New Zealand",
        "Wellington",
        "Pacific/Auckland",
        ("Pacific/Auckland", "Pacific/Chatham"),
    ),
    CountryTimezone(
        "PH", "Philippines", "Manila", "Asia/Manila", ("Asia/Manila",)
    ),
    CountryTimezone("PL", "Poland", "Warsaw", "Europe/Warsaw", ("Europe/Warsaw",)),
    CountryTimezone(
        "RU",
        "Russia",
        "Moscow",
        "Europe/Moscow",
        (
            "Europe/Moscow",
            "Europe/Kaliningrad",
            "Asia/Yekaterinburg",
            "Asia/Novosibirsk",
            "Asia/Irkutsk",
            "Asia/Vladivostok",
            "Asia/Kamchatka",
        ),
    ),
    CountryTimezone(
        "SA", "Saudi Arabia", "Riyadh", "Asia/Riyadh", ("Asia/Riyadh",)
    ),
    CountryTimezone(
        "SE", "Sweden", "Stockholm", "Europe/Stockholm", ("Europe/Stockholm",)
    ),
    CountryTimezone(
        "SG", "Singapore", "Singapore", "Asia/Singapore", ("Asia/Singapore",)
    ),
    CountryTimezone(
        "TH", "Thailand", "Bangkok", "Asia/Bangkok", ("Asia/Bangkok",)
    ),
    CountryTimezone(
        "TR", "Türkiye", "Ankara", "Europe/Istanbul", ("Europe/Istanbul",)
    ),
    CountryTimezone("TW", "Taiwan", "Taipei", "Asia/Taipei", ("Asia/Taipei",)),
    CountryTimezone(
        "US",
        "United States",
        "Washington, D.C.",
        "America/New_York",
        (
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "America/Anchorage",
            "Pacific/Honolulu",
        ),
    ),
    CountryTimezone(
        "ZA",
        "South Africa",
        "Pretoria",
        "Africa/Johannesburg",
        ("Africa/Johannesburg",),
    ),
)

_COUNTRY_INDEX = {
    key.casefold(): country
    for country in _COUNTRIES
    for key in (country.country_code, country.country_name)
}
_COUNTRY_INDEX["uk"] = _COUNTRY_INDEX["gb"]
_COUNTRY_INDEX["united states of america"] = _COUNTRY_INDEX["us"]
_COUNTRY_INDEX["uae"] = _COUNTRY_INDEX["ae"]
_CAPITAL_INDEX = {
    country.capital.casefold(): country for country in _COUNTRIES
}
_CAPITAL_INDEX["washington dc"] = _COUNTRY_INDEX["us"]
_CAPITAL_INDEX["hong kong"] = _COUNTRY_INDEX["hk"]


def _validate_timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {timezone_name}") from exc


def get_country(country: str) -> CountryTimezone:
    """Resolve a country by ISO-3166 alpha-2 code or supported country name."""
    result = _COUNTRY_INDEX.get(country.strip().casefold())
    if result is None:
        raise ValueError(f"Country is not in the timezone registry: {country}")
    return result


def get_country_timezone(country: str) -> ZoneInfo:
    """Return the timezone of the country's capital city."""
    return _validate_timezone(get_country(country).capital_timezone)


def get_capital_timezone(capital: str) -> ZoneInfo:
    """Resolve a registered national capital to its IANA timezone."""
    result = _CAPITAL_INDEX.get(capital.strip().casefold())
    if result is None:
        raise ValueError(f"Capital is not in the timezone registry: {capital}")
    return _validate_timezone(result.capital_timezone)


def get_country_timezones(country: str) -> tuple[ZoneInfo, ...]:
    """Return all registered timezones for a country, capital zone first."""
    return tuple(_validate_timezone(name) for name in get_country(country).timezones)


def to_country_local_time(timestamp: datetime, country: str) -> datetime:
    """Convert an aware timestamp to the country's capital local time."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Timestamp must be timezone-aware.")
    return timestamp.astimezone(get_country_timezone(country))


def to_capital_local_time(timestamp: datetime, capital: str) -> datetime:
    """Convert an aware timestamp to a registered capital's local time."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Timestamp must be timezone-aware.")
    return timestamp.astimezone(get_capital_timezone(capital))


def list_registered_countries() -> tuple[CountryTimezone, ...]:
    """Return the immutable country/capital timezone registry."""
    return _COUNTRIES
