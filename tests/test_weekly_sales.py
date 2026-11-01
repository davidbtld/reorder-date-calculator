"""Tests der Wochenaggregation gemäß Spezifikationsabschnitt 5.1."""

from datetime import date

import pandas as pd

from config import CHART_MONTHS
from core.weekly_sales import aggregate_weekly_sales


def test_aggregate_weekly_sales_sums_monday_through_sunday_and_fills_gaps() -> None:
    orders = pd.DataFrame(
        {
            "Paid at": [
                "2026-10-05 09:00:00",
                "2026-10-19 09:00:00",
                "2026-10-25 23:59:59",
                "2026-10-27 12:00:00",
            ],
            "Lineitem quantity": [1, 2, 3, 4],
        }
    )

    result = aggregate_weekly_sales(orders, today=date(2026, 11, 1))

    assert result.iloc[-2:]["week_start"].tolist() == [
        pd.Timestamp("2026-10-19"),
        pd.Timestamp("2026-10-26"),
    ]
    assert result.iloc[-2:]["quantity"].tolist() == [5, 4]
    assert result["quantity"].eq(0).any()


def test_aggregate_weekly_sales_shortens_period_to_first_available_sale() -> None:
    today = date(2026, 6, 18)
    orders = pd.DataFrame(
        {
            "Paid at": ["2026-06-17 08:37:12"],
            "Lineitem quantity": [7],
        }
    )

    result = aggregate_weekly_sales(orders, today=today)

    assert result["week_start"].tolist() == [pd.Timestamp("2026-06-15")]
    assert result["quantity"].tolist() == [7]


def test_aggregate_weekly_sales_uses_configured_month_window_and_includes_today() -> None:
    today = date(2026, 10, 26)
    chart_start = (
        pd.Timestamp(today) - pd.DateOffset(months=CHART_MONTHS)
    ).date()
    orders = pd.DataFrame(
        {
            "Paid at": [
                chart_start.isoformat(),
                (chart_start - pd.Timedelta(days=1)).isoformat(),
                today.isoformat(),
                "2026-10-27",
            ],
            "Lineitem quantity": [2, 100, 3, 200],
        }
    )

    result = aggregate_weekly_sales(orders, today=today)

    assert result["week_start"].iloc[0] == pd.Timestamp(
        chart_start - pd.Timedelta(days=chart_start.weekday())
    )
    assert result["week_start"].iloc[-1] == pd.Timestamp("2026-10-26")
    assert result["quantity"].sum() == 5


def test_aggregate_weekly_sales_returns_empty_frame_without_historical_dates() -> None:
    orders = pd.DataFrame(
        {
            "Paid at": ["not a date", "2026-10-27"],
            "Lineitem quantity": [1, 5],
        }
    )

    result = aggregate_weekly_sales(orders, today=date(2026, 10, 26))

    assert result.empty
    assert result.columns.tolist() == ["week_start", "quantity"]
