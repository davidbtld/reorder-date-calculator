"""Bereinigung der Bestellpositionen gemäß Spezifikationsschritt 4."""

import pandas as pd


def clean_order_lines(orders: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Entfernt Retouren und ungültige Mengen aus den Bestellzeilen.

    Entspricht Schritt 4 der funktionalen Spezifikation. Mengen werden
    numerisch interpretiert; Zeilen mit positiver Menge bleiben erhalten.

    Args:
        orders: Die nach dem Auffüllen gruppierten Bestellzeilen.

    Returns:
        Ein Tupel aus bereinigten Bestellzeilen, Anzahl der Retourenzeilen
        und Anzahl der Zeilen mit ungültiger Menge.
    """
    if orders.empty:
        return orders.copy(), 0, 0

    quantities = pd.to_numeric(orders["Lineitem quantity"], errors="coerce")
    return_count = int(quantities.lt(0).sum())
    invalid_quantity_count = int((quantities.isna() | quantities.eq(0)).sum())

    valid_mask = quantities.gt(0).to_numpy()
    cleaned_orders = orders.iloc[valid_mask].copy()
    cleaned_orders["Lineitem quantity"] = quantities.to_numpy()[valid_mask]

    return cleaned_orders, return_count, invalid_quantity_count
