"""Ergebnisdarstellung und Empfehlungskacheln gemäß Spezifikationsschritt 7."""

import streamlit as st

from core.pipeline import PipelineResult
from core.reorder import (
    ReorderRecommendation,
    calculate_reorder_point,
    classify_reorder_urgency,
)
from ui.formatting import format_date, format_date_range, format_number
from ui.result_state import get_result_display_state


def _render_notices(
    result: PipelineResult,
    recommendation: ReorderRecommendation | None,
    inventory: int | None,
) -> None:
    trend = result.trend
    warning_lines: list[str] = []
    if result.excluded_orders > 0:
        warning_lines.append(
            f"{format_number(result.excluded_orders, 0)} Bestellung(en) ohne "
            "gültiges Zahlungsdatum (Paid at leer oder nicht lesbar) aus der "
            "Analyse ausgeschlossen."
        )
    if result.return_lines > 0:
        warning_lines.append(
            f"{format_number(result.return_lines, 0)} Retouren im Datenzeitraum "
            "erkannt, nicht in Trend eingerechnet."
        )
    if result.invalid_quantity_lines > 0:
        warning_lines.append(
            f"{format_number(result.invalid_quantity_lines, 0)} Zeile(n) mit "
            "ungültiger Menge verworfen."
        )
    if trend.is_period_shortened:
        warning_lines.append(
            f"Die hochgeladene Datei deckt nur {trend.covered_days} Tage ab. "
            "Der berechnete Trend basiert auf einem verkürzten Zeitraum und "
            "kann weniger belastbar sein."
        )
    if warning_lines:
        st.warning("  \n".join(warning_lines))

    if (
        recommendation is not None
        and inventory is not None
        and recommendation.order_immediately
    ):
        reorder_point = recommendation.reorder_point
        st.error(
            "Bestellung muss SOFORT ausgelöst werden.  \n"
            f"Aktueller Lagerbestand {format_number(inventory, 0)} ≤ "
            f"Meldebestand {format_number(reorder_point, 1, False)}"
        )
    elif trend.total_quantity == 0:
        st.info(
            "Im gewählten Zeitraum wurden keine Verkäufe des Produkts erfasst. "
            "Eine Trendberechnung ist nicht möglich."
        )


def _render_status_badge(status: str, urgency: str | None) -> None:
    badge_state = urgency or "info"
    st.markdown(
        f'<span class="status-badge status-badge-{badge_state}">{status}</span>',
        unsafe_allow_html=True,
    )


def render_results(
    result: PipelineResult,
    inventory: int | None,
    lead_time_days: int | None,
    recommendation: ReorderRecommendation | None,
) -> None:
    """Zeigt verfügbare Analysewerte und bei vollständigen Angaben die Empfehlung."""
    display_state = get_result_display_state(inventory, lead_time_days)
    _render_notices(result, recommendation, inventory)
    if display_state.show_missing_inputs_notice:
        st.info("Bitte aktuellen Lagerbestand und Lieferzeit eingeben.")

    trend = result.trend
    columns = st.columns(
        [1.3, 1, 1, 1, 1]
        if display_state.show_main_card
        else [1] * (4 if display_state.show_reorder_point else 3),
        gap="small",
    )
    result_columns = iter(columns)

    if display_state.show_main_card:
        if recommendation is None or inventory is None:
            raise ValueError("Für die Hauptkachel fehlen vollständige Eingabewerte.")
        urgency = classify_reorder_urgency(
            days_until_reorder=recommendation.days_until_reorder,
            inventory=inventory,
            reorder_point=recommendation.reorder_point,
        )
        if recommendation.order_immediately:
            main_label = "Handlungsbedarf"
            main_value = "Jetzt bestellen"
            badge = "Sofort"
        elif trend.total_quantity == 0:
            main_label = "Spätestens bestellen am"
            main_value = "Keine Empfehlung"
            badge = "Keine Trendberechnung"
        elif recommendation.order_date is None:
            st.warning(
                "Der Bestand reicht rechnerisch über Jahrtausende – "
                "kein Bestelltermin berechenbar."
            )
            main_label = "Spätestens bestellen am"
            main_value = "Kein Datum verfügbar"
            badge = "Nicht verfügbar"
        else:
            days = recommendation.days_until_reorder
            main_label = "Spätestens bestellen am"
            main_value = format_date(recommendation.order_date)
            badge = "Heute" if days == 0 else (
                f"In {days} Tag" if days == 1 else f"In {days} Tagen"
            )
        with next(result_columns):
            card_key = f"main-card-{urgency or 'info'}"
            with st.container(border=True, key=card_key):
                st.metric(main_label, main_value)
                _render_status_badge(badge, urgency)

    with next(result_columns):
        with st.container(border=True, key="trend-card"):
            st.metric("Trend", format_number(trend.trend_per_day, 3, False))
            st.caption("Stück pro Tag")

    if display_state.show_reorder_point:
        with next(result_columns):
            with st.container(border=True, key="reorder-point-card"):
                if recommendation is not None:
                    reorder_point = recommendation.reorder_point
                elif lead_time_days is not None and trend.total_quantity > 0:
                    # Der Meldebestand bleibt auch ohne Lagerbestand berechenbar.
                    reorder_point = calculate_reorder_point(
                        trend.total_quantity,
                        trend.covered_days,
                        lead_time_days,
                    )
                else:
                    reorder_point = None
                reorder_value = (
                    format_number(reorder_point, 1, False)
                    if reorder_point is not None
                    else "Nicht berechnet"
                )
                st.metric("Meldebestand", reorder_value)
                st.caption("Stück · Bei diesem Bestand bestellen")

    with next(result_columns):
        with st.container(border=True, key="period-card"):
            st.metric("Datenzeitraum", f"{trend.covered_days} Tage")
            st.caption(
                format_date_range(trend.effective_start, trend.end_date)
            )

    with next(result_columns):
        with st.container(border=True, key="considered-card"):
            st.metric("Berücksichtigt", format_number(result.considered_rows, 0))
            st.caption(
                f"Zeilen · {format_number(result.considered_orders, 0)} Bestellungen"
            )
