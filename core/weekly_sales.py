"""Wochenabsatz-Aggregation gemäß Spezifikationsabschnitt 5.1."""

from datetime import date, datetime

import pandas as pd

from config import CHART_MONTHS
from core.dates import calendar_date


def aggregate_weekly_sales(orders: pd.DataFrame, today: date) -> pd.DataFrame:
    """Aggregiert bereinigte Bestellzeilen für Abschnitt 5.1 der Spezifikation.

    Die Wochen beginnen montags. Der Diagrammzeitraum reicht von sechs
    konfigurierten Monaten vor ``today`` bis einschließlich heute, verkürzt
    sich aber auf das früheste vorhandene Verkaufsdatum, wenn die Datei
    weniger weit zurückreicht.

    Args:
        orders: Bereinigte Zeilen mit „Paid at“ und „Lineitem quantity“.
        today: Einschließliches Ende des Diagrammzeitraums.

    Returns:
        Datenrahmen mit den Spalten ``week_start`` (Wochenbeginn als Zeitstempel)
        und ``quantity`` (verkaufte Stückzahl). Wochen ohne Verkäufe erhalten 0.

    Raises:
        ValueError: Wenn Pflichtspalten fehlen oder ``today`` kein Datum ist.
    """
    required_columns = {"Paid at", "Lineitem quantity"}
    missing_columns = required_columns.difference(orders.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Erforderliche Spalten fehlen: {missing}.")
    if not isinstance(today, date) or isinstance(today, datetime):
        raise ValueError("Das Referenzdatum 'today' muss ein Datum sein.")

    empty_result = pd.DataFrame(
        {
            "week_start": pd.Series(dtype="datetime64[ns]"),
            "quantity": pd.Series(dtype="int64"),
        }
    )
    if orders.empty:
        return empty_result

    paid_dates = [calendar_date(value) for value in orders["Paid at"]]
    available_dates = [
        paid_date for paid_date in paid_dates if paid_date is not None and paid_date <= today
    ]
    if not available_dates:
        return empty_result

    chart_start = (pd.Timestamp(today) - pd.DateOffset(months=CHART_MONTHS)).date()
    effective_start = max(chart_start, min(available_dates))
    # Wochen beginnen montags; der früheste Verkauf begrenzt den Diagrammzeitraum.
    first_week = pd.Timestamp(
        effective_start - pd.Timedelta(days=effective_start.weekday())
    )
    last_week = pd.Timestamp(today - pd.Timedelta(days=today.weekday()))
    # Die laufende Woche bleibt sichtbar, obwohl ihre Verkäufe noch unvollständig sind.
    week_starts = pd.date_range(first_week, last_week, freq="W-MON")

    included_indices = [
        index
        for index, paid_date in enumerate(paid_dates)
        if paid_date is not None and effective_start <= paid_date <= today
    ]
    quantities = pd.to_numeric(
        orders["Lineitem quantity"].iloc[included_indices], errors="raise"
    )
    sales = pd.DataFrame(
        {
            "week_start": [
                pd.Timestamp(
                    paid_dates[index]
                    - pd.Timedelta(days=paid_dates[index].weekday())
                )
                for index in included_indices
            ],
            "quantity": quantities.to_numpy(),
        }
    )
    weekly_sales = sales.groupby("week_start")["quantity"].sum()
    # Fehlende Wochen bleiben sichtbar und tragen mit null zum Diagramm bei.
    weekly_sales = weekly_sales.reindex(week_starts, fill_value=0)

    return pd.DataFrame(
        {
            "week_start": weekly_sales.index,
            "quantity": weekly_sales.to_numpy(),
        }
    ).reset_index(drop=True)
