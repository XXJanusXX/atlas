from datetime import UTC, datetime

import pytest

from atlas.timezones import (
    get_capital_timezone,
    get_country,
    get_country_timezone,
    get_country_timezones,
    list_registered_countries,
    to_country_local_time,
)


def test_country_code_and_name_resolve_to_capital_timezone() -> None:
    assert get_country("SG").capital == "Singapore"
    assert get_country("Singapore").capital_timezone == "Asia/Singapore"
    assert str(get_country_timezone("IN")) == "Asia/Kolkata"


def test_capital_lookup_resolves_timezone() -> None:
    assert str(get_capital_timezone("Tokyo")) == "Asia/Tokyo"


def test_multi_timezone_country_returns_all_zones() -> None:
    zones = get_country_timezones("US")
    assert str(zones[0]) == "America/New_York"
    assert "America/Los_Angeles" in {str(zone) for zone in zones}


def test_country_local_conversion_handles_dst() -> None:
    winter = datetime(2026, 1, 15, 12, tzinfo=UTC)
    summer = datetime(2026, 7, 15, 12, tzinfo=UTC)
    assert to_country_local_time(winter, "GB").hour == 12
    assert to_country_local_time(summer, "GB").hour == 13


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        to_country_local_time(datetime(2026, 1, 1, 12), "SG")


def test_unknown_country_and_capital_fail_explicitly() -> None:
    with pytest.raises(ValueError, match="Country is not"):
        get_country("Atlantis")
    with pytest.raises(ValueError, match="Capital is not"):
        get_capital_timezone("Unknown City")


def test_registry_uses_valid_iana_timezones() -> None:
    for country in list_registered_countries():
        assert str(get_country_timezone(country.country_code)) == country.capital_timezone
        assert len(get_country_timezones(country.country_code)) == len(country.timezones)
