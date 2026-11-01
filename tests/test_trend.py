"""Tests der Trend- und Abdeckungsberechnung gemäß Spezifikationsschritten 5 und 6."""

from datetime import date, timedelta

import pandas as pd

from config import TREND_WINDOW_DAYS
from core.trend import calculate_trend


def _orders(paid_at: list[object], quantities: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Paid at": paid_at,
            "Lineitem quantity": quantities,
        }
    )


def test_calculate_trend_uses_architecture_reference_data() -> None:
    orders = _orders(
        [
            "2026-06-17 08:37:12",
            "2026-06-17 08:37:12",
            "2026-06-17 08:37:12",
            "2026-06-17 08:37:12",
            "2026-05-25 15:38:36",
            "2026-05-14 21:27:23",
            "2026-04-09 11:57:59",
        ],
        [1] * 7,
    )

    result = calculate_trend(orders, today=date(2026, 6, 18))

    assert result.total_quantity == 7
    assert result.covered_days == 71
    assert result.effective_start == date(2026, 4, 9)
    assert result.end_date == date(2026, 6, 18)
    assert result.trend_per_day == 7 / 71
    assert result.is_period_shortened is True


def test_calculate_trend_caps_coverage_at_configured_window() -> None:
    today = date(2026, 6, 18)
    window_start = today - timedelta(days=TREND_WINDOW_DAYS - 1)
    day_before_window = window_start - timedelta(days=1)
    orders = _orders(
        [day_before_window, window_start, today],
        [20, 2, 1],
    )

    result = calculate_trend(orders, today=today)

    assert result.total_quantity == 3
    assert result.covered_days == TREND_WINDOW_DAYS
    assert result.effective_start == window_start
    assert result.is_period_shortened is False


def test_calculate_trend_single_sale_day_has_one_covered_day() -> None:
    today = date(2026, 6, 18)

    result = calculate_trend(
        _orders([today], [3]),
        today=today,
    )

    assert result.total_quantity == 3
    assert result.covered_days == 1
    assert result.effective_start == today
    assert result.trend_per_day == 3
    assert result.is_period_shortened is True


def test_calculate_trend_returns_zero_when_no_sales_are_in_window() -> None:
    result = calculate_trend(
        _orders([date(2025, 1, 1)], [4]),
        today=date(2026, 6, 18),
    )

    assert result.total_quantity == 0
    assert result.trend_per_day == 0
    assert result.covered_days == TREND_WINDOW_DAYS
    assert result.is_period_shortened is False


def test_calculate_trend_ignores_dates_after_today() -> None:
    today = date(2026, 6, 18)

    result = calculate_trend(
        _orders([today, date(2026, 6, 19)], [2, 50]),
        today=today,
    )

    assert result.total_quantity == 2
    assert result.effective_start == today
    assert result.covered_days == 1
    assert result.trend_per_day == 2


def test_calculate_trend_counts_window_start_but_not_previous_day() -> None:
    today = date(2026, 6, 18)
    window_start = today - timedelta(days=TREND_WINDOW_DAYS - 1)
    day_before_window = window_start - timedelta(days=1)

    result = calculate_trend(
        _orders([day_before_window, window_start], [100, 2]),
        today=today,
    )

    assert result.total_quantity == 2
    assert result.effective_start == window_start
    assert result.covered_days == TREND_WINDOW_DAYS
    assert result.is_period_shortened is False


def test_calculate_trend_compares_timestamp_calendar_date_without_timezone_conversion() -> None:
    today = date(2026, 6, 18)
    window_start = today - timedelta(days=TREND_WINDOW_DAYS - 1)
    timestamp = f"{window_start.isoformat()} 00:30:00+14:00"

    result = calculate_trend(
        _orders([timestamp], [1]),
        today=today,
    )

    assert result.total_quantity == 1
    assert result.effective_start == window_start
