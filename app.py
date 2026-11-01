"""Streamlit-Anwendung zur Lageranalyse gemäß Spezifikationsschritten 1 bis 7."""

from datetime import date
from io import BytesIO

import streamlit as st

from config import APP_TITLE, DEMO_MODE
from core.filtering import get_distinct_product_names
from core.pipeline import (
    PipelineResult,
    calculate_analysis_recommendation,
    run_analysis_pipeline,
)
from data.loader import load_orders
from ui.chart import render_weekly_chart
from ui.inputs import render_parameters, render_upload
from ui.results import render_results
from ui.theme import apply_theme


@st.cache_data(show_spinner=False)
def _load_orders_cached(file_content: bytes, filename: str):
    """Lädt und validiert Upload-Daten im Streamlit-Arbeitsspeicher-Cache."""
    # Der Dateiinhalt bestimmt den Schlüssel und vermeidet erneutes Einlesen.
    upload = BytesIO(file_content)
    upload.name = filename
    return load_orders(upload)


@st.cache_data(show_spinner="Daten werden analysiert …")
def _run_pipeline_cached(
    file_content: bytes,
    filename: str,
    selected_products: tuple[str, ...],
    today: date,
) -> PipelineResult:
    """Zwischenspeichert die datei- und produktabhängige Analyse."""
    # Lagerbestand und Lieferzeit ändern die Analyse nicht.
    orders = _load_orders_cached(file_content, filename)
    return run_analysis_pipeline(orders, list(selected_products), today)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📦", layout="wide")
    apply_theme()
    st.markdown(
        """
        <div class="app-header">
            <div class="app-content-shell">
                <div class="app-content-container">
                    <span class="logo-placeholder">LOGO</span>
                    <span class="app-header-title">Lageranalyse</span>
                </div>
            </div>
        </div>
        <div class="app-content-shell">
            <div class="app-content-container page-heading">
                <h1>Bestellzeitpunkt ermitteln</h1>
                <p>Shopify-Bestellexport hochladen, Produkt wählen, Lagerbestand und Lieferzeit angeben</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True, key="filter-card"):
        upload_column, product_column, inventory_column, lead_time_column = (
            st.columns([1.2, 1.55, 1.8, 0.85], gap="small")
        )
        uploaded_file = render_upload(upload_column)
        orders = None
        product_names: list[str] = []
        load_error: str | None = None
        if uploaded_file is not None:
            file_content = uploaded_file.getvalue()
            filename = uploaded_file.name
            try:
                orders = _load_orders_cached(file_content, filename)
            except (ValueError, FileNotFoundError) as error:
                load_error = str(error)
            else:
                try:
                    product_names = get_distinct_product_names(orders)
                except (AttributeError, KeyError, ValueError):
                    load_error = (
                        "In der Datei wurden keine lesbaren Produktnamen gefunden."
                    )

        selected_products, inventory, lead_time_days = render_parameters(
            product_names,
            product_column,
            inventory_column,
            lead_time_column,
        )

    if DEMO_MODE:
        # Der Hinweis schützt vor versehentlichem Hochladen echter Shop-Daten.
        st.info(
            "Dies ist eine Demo, bitte keine echten Shop-Daten hochladen. "
            "Verwende ausschließlich erfundene Beispieldaten."
        )

    if load_error is not None:
        st.error(load_error)
    elif uploaded_file is None:
        st.info("Lade eine CSV- oder XLSX-Datei hoch, um zu beginnen.")
    elif not product_names:
        st.info("Die Datei enthält keine auswählbaren Produktnamen.")
    elif not selected_products:
        st.info("Bitte mindestens einen Produktnamen auswählen.")
    else:
        today = date.today()
        try:
            result = _run_pipeline_cached(
                uploaded_file.getvalue(),
                uploaded_file.name,
                tuple(selected_products),
                today,
            )
            # Eingaben ändern nur die Empfehlung; Analyse und Diagramm bleiben zwischengespeichert.
            recommendation = (
                calculate_analysis_recommendation(
                    result,
                    inventory=inventory,
                    lead_time_days=lead_time_days,
                    today=today,
                )
                if inventory is not None and lead_time_days is not None
                else None
            )
        except ValueError as error:
            st.error(str(error))
        else:
            render_results(result, inventory, lead_time_days, recommendation)
            render_weekly_chart(result, today)

    st.markdown(
        """
        <footer class="app-footer">
            <div class="app-content-shell">
                <div class="app-content-container">
                    Alle Angaben ohne Gewähr · Daten werden nur lokal verarbeitet und nicht gespeichert.
                </div>
            </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
