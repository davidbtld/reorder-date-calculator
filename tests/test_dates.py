"""Tests der gemeinsamen Kalenderdatums-Konvertierung für Schritte 3, 5 und 6."""

from datetime import date, datetime

import pytest

from core.dates import calendar_date


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-06-18 00:30:00+14:00", date(2026, 6, 18)),
        (date(2026, 6, 18), date(2026, 6, 18)),
        (datetime(2026, 6, 18, 12, 30), date(2026, 6, 18)),
    ],
)
def test_calendar_date_returns_calendar_date_without_timezone_conversion(
    value: object,
    expected: date,
) -> None:
    assert calendar_date(value) == expected


@pytest.mark.parametrize("value", ["not a date", None, 42])
def test_calendar_date_returns_none_for_invalid_values(value: object) -> None:
    assert calendar_date(value) is None
