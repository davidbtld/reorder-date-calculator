"""Bestellgruppenbildung gemäß Spezifikationsschritt 3."""

import pandas as pd

from core.dates import calendar_date


def group_orders_by_name(orders: pd.DataFrame) -> tuple[pd.DataFrame, pd.Index]:
    """Füllt Paid-at-Werte je Bestellung auf und meldet ungültige Gruppen.

    Entspricht Schritt 3 der funktionalen Spezifikation.

    Args:
        orders: Alle eingelesenen Bestellzeilen, ungefiltert nach Produkt.

    Returns:
        Ein Tupel aus den gültigen, unveränderten Bestellzeilen mit
        aufgefüllter Spalte „Paid at“ und den Bestellnummern ohne gültiges
        Zahlungsdatum.
    """
    if orders.empty:
        return orders.copy(), pd.Index([])

    paid_at_values = orders["Paid at"].to_numpy(dtype=object)
    parseable_paid_at = orders["Paid at"].map(
        lambda value: calendar_date(value) is not None
    ).to_numpy()

    group_names = pd.Series(orders["Name"].to_numpy(dtype=object))
    # Nur parsebare Werte dürfen andere Zeilen derselben Bestellung ergänzen.
    valid_paid_at = pd.Series(paid_at_values, dtype=object).where(parseable_paid_at)
    # Das erste gültige Datum wird auf alle Positionen der Bestellung übertragen.
    first_paid_at = valid_paid_at.groupby(
        group_names,
        sort=False,
        dropna=False,
    ).transform("first")

    valid_rows = first_paid_at.notna().to_numpy()
    grouped_orders = orders.iloc[valid_rows].copy()
    grouped_orders["Paid at"] = first_paid_at.iloc[valid_rows].to_numpy()

    first_paid_at_by_order = first_paid_at.groupby(
        group_names,
        sort=False,
        dropna=False,
    ).first()
    invalid_order_names = first_paid_at_by_order.index[
        first_paid_at_by_order.isna()
    ]
    return grouped_orders, invalid_order_names
