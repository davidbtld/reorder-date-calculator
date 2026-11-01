"""Eingabebausteine der Oberfläche gemäß Spezifikationsschritten 1, 2 und 7."""

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from config import MAX_INVENTORY, MAX_LEAD_TIME_DAYS


def render_upload(upload_column: DeltaGenerator):
    """Zeigt den Datei-Upload für CSV- und XLSX-Bestellexporte."""
    with upload_column:
        return st.file_uploader(
            "Bestellexport (CSV oder XLSX)",
            type=["csv", "xlsx"],
            help="Unterstützt CSV- und Excel-Dateien im .xlsx-Format.",
        )


def render_parameters(
    product_names: list[str],
    product_column: DeltaGenerator,
    inventory_column: DeltaGenerator,
    lead_time_column: DeltaGenerator,
) -> tuple[list[str], int | None, int | None]:
    """Zeigt Produktauswahl, Lagerbestand und Lieferzeit."""
    with product_column:
        selected_products = st.multiselect(
            "Produkt(e)",
            options=product_names,
            placeholder="Produkte auswählen",
            help="Wähle die vorhandenen Lineitem-Namen aus, die gemeinsam analysiert werden.",
            disabled=not product_names,
        )
    with inventory_column:
        inventory = st.number_input(
            "Aktueller Lagerbestand (Stk)",
            min_value=0,
            max_value=MAX_INVENTORY,
            value=None,
            step=1,
        )
    with lead_time_column:
        lead_time_days = st.number_input(
            "Lieferzeit (Tage)",
            min_value=0,
            max_value=MAX_LEAD_TIME_DAYS,
            value=None,
            step=1,
        )
    return (
        selected_products,
        int(inventory) if inventory is not None else None,
        int(lead_time_days) if lead_time_days is not None else None,
    )
