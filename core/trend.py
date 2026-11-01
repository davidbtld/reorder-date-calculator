"""Trend- und Abdeckungsberechnung gemäß Spezifikationsschritten 5 und 6."""

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from config import TREND_WINDOW_DAYS
from core.dates import calendar_date


@dataclass(frozen=True)
class TrendResult:
    """Typisiertes Ergebnis der Abdeckungs- und Trendberechnung."""

    trend_per_day: float
    covered_days: int
    effective_start: date
    end_date: date
    total_quantity: float
    is_period_shortened: bool


def calculate_trend(orders: pd.DataFrame, today: date) -> TrendResult:
    """Prüft die Datenabdeckung und berechnet den durchschnittlichen Tagestrend.

    Entspricht den Schritten 5 und 6 der funktionalen Spezifikation.

    Args:
        orders: Bereinigte Bestellzeilen mit „Paid at“ und „Lineitem quantity“.
        today: Ende des Trendfensters; das Systemdatum wird nicht selbst abgefragt.

    Returns:
        Trend, Abdeckung, effektiver Zeitraum, Summe der Mengen und
        Kennzeichen für einen verkürzten Zeitraum.

    Raises:
        ValueError: Wenn Pflichtspalten fehlen oder Fenster-Mengen ungültig sind.
    """
    required_columns = {"Paid at", "Lineitem quantity"}
    missing_columns = required_columns.difference(orders.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Erforderliche Spalten fehlen: {missing}.")

    # Das Fenster enthält heute und insgesamt genau TREND_WINDOW_DAYS Kalendertage.
    window_start = today - timedelta(days=TREND_WINDOW_DAYS - 1)
    paid_dates = [calendar_date(value) for value in orders["Paid at"]]
    included_indices = [
        index
        for index, paid_date in enumerate(paid_dates)
        if paid_date is not None and window_start <= paid_date <= today
    ]
    included_dates = [paid_dates[index] for index in included_indices]
    # Der Trend beginnt beim frühesten Verkauf im Fenster, andernfalls am Fensteranfang.
    effective_start = min(included_dates) if included_dates else window_start
    # +1 zählt Anfangs- und Enddatum als abgedeckte Kalendertage mit.
    covered_days = (today - effective_start).days + 1

    quantities = pd.to_numeric(
        orders["Lineitem quantity"].iloc[included_indices],
        errors="raise",
    )
    if quantities.isna().any():
        raise ValueError("Mengen im Trendfenster dürfen nicht leer sein.")

    total_quantity = float(quantities.sum())
    return TrendResult(
        trend_per_day=total_quantity / covered_days,
        covered_days=covered_days,
        effective_start=effective_start,
        end_date=today,
        total_quantity=total_quantity,
        is_period_shortened=covered_days < TREND_WINDOW_DAYS,
    )
