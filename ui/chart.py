"""Wochendiagramm gemäß Spezifikationsabschnitt 5.1."""

from datetime import date, timedelta
from math import floor

import altair as alt
import pandas as pd
import streamlit as st

from config import (
    COLOR_GRID,
    COLOR_MUTED,
    COLOR_PRIMARY,
    COLOR_TREND_WINDOW,
    TREND_WINDOW_DAYS,
)
from core.pipeline import PipelineResult


def render_weekly_chart(result: PipelineResult, today: date) -> None:
    """Zeigt Wochenabsatz mit blau markiertem 90-Tage-Trendfenster."""
    weekly_sales = result.weekly_sales
    with st.container(border=True, key="chart-card"):
        st.markdown('<p class="chart-card-title">Absatz pro Woche</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="chart-card-subtitle">Letzte 6 Monate · Kalenderwochen · '
            "laufende Woche bis heute</p>",
            unsafe_allow_html=True,
        )
        if weekly_sales.empty:
            st.info("Für den Diagrammzeitraum liegen keine auswertbaren Verkaufsdaten vor.")
            return

        chart_data = weekly_sales.copy()
        chart_data["week_index"] = range(len(chart_data))
        first_week = chart_data.iloc[0]["week_start"].date()
        last_week = chart_data.iloc[-1]["week_start"].date()
        first_week_label = f"KW {first_week.isocalendar().week}"
        last_week_label = f"KW {last_week.isocalendar().week}"

        window_start = today - timedelta(days=TREND_WINDOW_DAYS - 1)
        start_index = max(0, (window_start - first_week).days / 7)
        end_index = min(len(chart_data) - 1, (today - first_week).days / 7)
        trend_window = pd.DataFrame(
            {"start": [start_index], "end": [end_index]}
        )
        axis_expression = (
            f"datum.value === 0 ? '{first_week_label}' : "
            f"datum.value === {len(chart_data) - 1} ? '{last_week_label}' : ''"
        )

        background = (
            alt.Chart(trend_window)
            .mark_rect(color=COLOR_TREND_WINDOW, opacity=0.8)
            .encode(
                x=alt.X("start:Q"),
                x2=alt.X2("end:Q"),
            )
        )
        x_axis = alt.X(
            "week_index:Q",
            title="Kalenderwoche",
            scale=alt.Scale(domain=[0, max(1, len(chart_data) - 1)]),
            axis=alt.Axis(
                values=[0, len(chart_data) - 1],
                labelExpr=axis_expression,
                labelAngle=0,
                grid=False,
            ),
        )
        max_quantity = max(float(chart_data["quantity"].max()), 1)
        next_ten = (floor(max_quantity / 10) + 1) * 10
        axis_max = next_ten + 5
        y_axis = alt.Y(
            "quantity:Q",
            title="Stück pro Woche",
            scale=alt.Scale(domain=[0, axis_max], nice=False),
            axis=alt.Axis(format=".0f", tickMinStep=10),
        )
        line = (
            alt.Chart(chart_data)
            .mark_line(color=COLOR_PRIMARY, strokeWidth=2)
            .encode(
                x=x_axis,
                y=y_axis,
                tooltip=[
                    alt.Tooltip(
                        "week_start:T",
                        title="Wochenbeginn",
                        format="%d.%m.%Y",
                    ),
                    alt.Tooltip("quantity:Q", title="Stück", format=",.0f"),
                ],
            )
        )
        points = (
            alt.Chart(chart_data)
            .mark_point(color=COLOR_PRIMARY, filled=True, size=32)
            .encode(x=x_axis, y=y_axis)
        )
        trend_label_data = pd.DataFrame(
            {
                "week_index": [(start_index + end_index) / 2],
                "label_y": [next_ten + 2],
            }
        )
        trend_label = (
            alt.Chart(trend_label_data)
            .mark_text(text="Trendfenster (90 Tage)", color=COLOR_PRIMARY, dy=-4)
            .encode(
                x=alt.X("week_index:Q"),
                y=alt.Y(
                    "label_y:Q",
                    scale=alt.Scale(domain=[0, axis_max], nice=False),
                ),
            )
        )
        chart = (
            alt.layer(background, line, points, trend_label)
            .properties(height=300)
            .configure_view(stroke=None)
            .configure_axis(
                labelColor=COLOR_MUTED,
                titleColor=COLOR_MUTED,
                gridColor=COLOR_GRID,
            )
        )
        st.altair_chart(chart, width="stretch")
