"""Tests der Ergebnisformatierung gemäß Spezifikationsschritt 7."""

from datetime import date

import pytest

from ui.formatting import format_date, format_date_range, format_number


def test_format_date_uses_german_day_month_year_order() -> None:
    assert format_date(date(2026, 11, 3)) == "03.11.2026"


def test_format_date_range_uses_compact_start_date_in_same_year() -> None:
    assert format_date_range(date(2026, 7, 31), date(2026, 10, 28)) == (
        "31.07. – 28.10.2026"
    )


def test_format_date_range_shows_both_years_when_they_differ() -> None:
    assert format_date_range(date(2025, 12, 31), date(2026, 1, 2)) == (
        "31.12.2025 – 02.01.2026"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (120, "120"),
        (3.2, "3,2"),
        (67.2, "67,2"),
        (1234.56, "1.234,56"),
        (1234.0, "1.234"),
    ],
)
def test_format_number_uses_german_separators(
    value: int | float,
    expected: str,
) -> None:
    assert format_number(value) == expected


def test_format_number_respects_requested_decimal_places() -> None:
    assert format_number(1.256, max_decimal_places=1) == "1,3"
    assert format_number(1234.5, max_decimal_places=0) == "1.235"
    assert format_number(3.2, max_decimal_places=3, trim_trailing_zeros=False) == (
        "3,200"
    )
    assert format_number(67.2, max_decimal_places=1, trim_trailing_zeros=False) == (
        "67,2"
    )
