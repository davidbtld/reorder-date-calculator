"""Verknüpfung der Analyseschritte 2 bis 7 der funktionalen Spezifikation."""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from core.cleaning import clean_order_lines
from core.filtering import filter_by_selected_products
from core.grouping import group_orders_by_name
from core.reorder import ReorderRecommendation, calculate_reorder_recommendation
from core.trend import TrendResult, calculate_trend
from core.weekly_sales import aggregate_weekly_sales


@dataclass(frozen=True)
class PipelineResult:
    """Typisiertes Ergebnis der Schritte 2–6 und der Wochenaggregation."""

    trend: TrendResult
    weekly_sales: pd.DataFrame
    excluded_orders: int
    return_lines: int
    invalid_quantity_lines: int
    considered_rows: int
    considered_orders: int


def run_analysis_pipeline(
    orders: pd.DataFrame,
    selected_products: list[str],
    today: date,
) -> PipelineResult:
    """Führt Gruppierung, Produktfilter, Bereinigung, Trend und Wochenaggregation aus.

    Entspricht den Schritten 2–6 der funktionalen Spezifikation sowie
    Abschnitt 5.1 für die wöchentlichen Diagrammwerte.

    Args:
        orders: Eingelesene Shopify-Bestellzeilen.
        selected_products: Zur Analyse ausgewählte Produktnamen.
        today: Festes Referenzdatum für Trend und Wochenwerte.

    Returns:
        Trends, Wochenwerte und Zählwerte für die Ergebnis- und Hinweisflächen.

    Raises:
        ValueError: Wenn keine Produkte ausgewählt wurden oder keine Zeilen
            zu den ausgewählten Produkten passen.
    """
    if not selected_products:
        raise ValueError("Bitte mindestens einen Produktnamen auswählen.")

    # Gruppierung vor dem Produktfilter erhält Zahlungsdaten, die nur in einer
    # anderen Position derselben Bestellung stehen.
    grouped_orders, invalid_order_names = group_orders_by_name(orders)
    # Die ursprünglichen Zeilen bestimmen, ob ausgewählte Produkte überhaupt existieren.
    selected_orders = filter_by_selected_products(orders, selected_products)
    if selected_orders.empty:
        raise ValueError("Keine Datensätze für die ausgewählten Produkte gefunden.")

    # Nach dem Auffüllen werden nur die ausgewählten Produktpositionen analysiert.
    filtered_orders = filter_by_selected_products(grouped_orders, selected_products)
    # Ausschlüsse zählen nur Bestellungen mit mindestens einer ausgewählten Position.
    excluded_orders = int(
        selected_orders.loc[
            selected_orders["Name"].isin(invalid_order_names), "Name"
        ].nunique(dropna=False)
    )
    cleaned_orders, return_lines, invalid_quantity_lines = clean_order_lines(
        filtered_orders
    )
    trend = calculate_trend(cleaned_orders, today)
    weekly_sales = aggregate_weekly_sales(cleaned_orders, today)

    return PipelineResult(
        trend=trend,
        weekly_sales=weekly_sales,
        excluded_orders=excluded_orders,
        return_lines=return_lines,
        invalid_quantity_lines=invalid_quantity_lines,
        considered_rows=len(cleaned_orders),
        considered_orders=int(cleaned_orders["Name"].nunique(dropna=False)),
    )


def calculate_analysis_recommendation(
    result: PipelineResult,
    inventory: int,
    lead_time_days: int,
    today: date,
) -> ReorderRecommendation:
    """Berechnet Schritt 7 separat aus Trendresultat und aktuellen Eingaben."""
    return calculate_reorder_recommendation(
        total_quantity=result.trend.total_quantity,
        covered_days=result.trend.covered_days,
        inventory=inventory,
        lead_time_days=lead_time_days,
        today=today,
    )
