"""Produktauswahl und Filterung gemäß Spezifikationsschritt 2."""

import pandas as pd


def get_distinct_product_names(orders: pd.DataFrame) -> list[str]:
    """Liefert die sortierten, eindeutigen und bereinigten Produktnamen."""
    return sorted(orders["Lineitem name"].str.strip().dropna().unique())


def filter_by_selected_products(
    orders: pd.DataFrame, selected_products: list[str]
) -> pd.DataFrame:
    """Behält Zeilen, deren bereinigter Produktname genau einer Auswahl entspricht."""
    trimmed_names = orders["Lineitem name"].str.strip()
    trimmed_selection = [product.strip() for product in selected_products]
    return orders[trimmed_names.isin(trimmed_selection)]
