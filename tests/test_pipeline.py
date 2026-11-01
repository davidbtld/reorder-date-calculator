"""Tests der Analyseschritte 2 bis 7 und ihrer Verknüpfung."""

from datetime import date

import pandas as pd
import pytest

from core.pipeline import (
    calculate_analysis_recommendation,
    run_analysis_pipeline,
)


def _reference_orders() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Name": [
                "#1003",
                "#1003",
                "#1003",
                "#1003",
                "#1002",
                "#1001",
                "#1000",
                "#0999",
                "#0999",
            ],
            "Paid at": [
                "2026-06-17 08:37:12",
                None,
                None,
                None,
                "2026-05-25 15:38:36",
                "2026-05-14 21:27:23",
                "2026-04-09 11:57:59",
                "2026-03-10 17:18.21",
                None,
            ],
            "Lineitem quantity": [1] * 9,
            "Lineitem name": ["Fictional bottle"] * 9,
        }
    )


def test_run_analysis_pipeline_matches_architecture_reference_data() -> None:
    result = run_analysis_pipeline(
        _reference_orders(),
        selected_products=["Fictional bottle"],
        today=date(2026, 6, 18),
    )

    assert result.excluded_orders == 1
    assert result.return_lines == 0
    assert result.invalid_quantity_lines == 0
    assert result.considered_rows == 7
    assert result.considered_orders == 4
    assert result.trend.total_quantity == 7
    assert result.weekly_sales["quantity"].sum() == 7


def test_run_analysis_pipeline_counts_returns_and_invalid_quantities() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-01", "#SYNTH-02", "#SYNTH-03", "#SYNTH-04"],
            "Paid at": ["2026-10-26"] * 4,
            "Lineitem quantity": [2, -1, 0, "unknown"],
            "Lineitem name": ["Fictional mug"] * 4,
        }
    )

    result = run_analysis_pipeline(
        orders, selected_products=["Fictional mug"], today=date(2026, 10, 26)
    )

    assert result.return_lines == 1
    assert result.invalid_quantity_lines == 2
    assert result.considered_rows == 1
    assert result.considered_orders == 1
    assert result.trend.total_quantity == 2


def test_pipeline_fills_paid_at_before_filtering_selected_product() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-10", "#SYNTH-10"],
            "Paid at": ["2026-10-28 09:30:00", None],
            "Lineitem quantity": [1, 3],
            "Lineitem name": ["Unselected product", "Selected product"],
        }
    )

    result = run_analysis_pipeline(
        orders, selected_products=["Selected product"], today=date(2026, 10, 28)
    )

    assert result.excluded_orders == 0
    assert result.considered_rows == 1
    assert result.considered_orders == 1
    assert result.trend.total_quantity == 3
    assert result.weekly_sales["quantity"].sum() == 3


def test_pipeline_does_not_count_invalid_date_order_without_selected_product() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-11", "#SYNTH-12"],
            "Paid at": ["not-a-date", "2026-10-28"],
            "Lineitem quantity": [1, 2],
            "Lineitem name": ["Unselected product", "Selected product"],
        }
    )

    result = run_analysis_pipeline(
        orders, selected_products=["Selected product"], today=date(2026, 10, 28)
    )

    assert result.excluded_orders == 0
    assert result.considered_rows == 1
    assert result.trend.total_quantity == 2


def test_pipeline_counts_invalid_date_order_with_selected_product() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-13", "#SYNTH-13"],
            "Paid at": ["not-a-date", None],
            "Lineitem quantity": [1, 1],
            "Lineitem name": ["Selected product", "Unselected product"],
        }
    )

    result = run_analysis_pipeline(
        orders, selected_products=["Selected product"], today=date(2026, 10, 28)
    )

    assert result.excluded_orders == 1
    assert result.considered_rows == 0
    assert result.considered_orders == 0
    assert result.trend.total_quantity == 0
    assert result.weekly_sales.empty


def test_pipeline_keeps_multiple_selected_products_in_same_order() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-14", "#SYNTH-14", "#SYNTH-14"],
            "Paid at": ["2026-10-28", None, None],
            "Lineitem quantity": [1, 2, 3],
            "Lineitem name": [
                "Selected product A",
                "Selected product B",
                "Unselected product",
            ],
        }
    )

    result = run_analysis_pipeline(
        orders,
        selected_products=["Selected product A", "Selected product B"],
        today=date(2026, 10, 28),
    )

    assert result.excluded_orders == 0
    assert result.considered_rows == 2
    assert result.considered_orders == 1
    assert result.trend.total_quantity == 3
    assert result.weekly_sales["quantity"].sum() == 3


def test_recommendation_can_be_recomputed_from_cached_pipeline_result() -> None:
    result = run_analysis_pipeline(
        _reference_orders(),
        selected_products=["Fictional bottle"],
        today=date(2026, 6, 18),
    )

    low_inventory = calculate_analysis_recommendation(
        result, inventory=0, lead_time_days=7, today=date(2026, 6, 18)
    )
    high_inventory = calculate_analysis_recommendation(
        result, inventory=100, lead_time_days=7, today=date(2026, 6, 18)
    )

    assert low_inventory.order_immediately is True
    assert high_inventory.order_immediately is False
    assert low_inventory.reorder_point == high_inventory.reorder_point
    assert result.trend.total_quantity == 7


@pytest.mark.parametrize(
    ("selected_products", "message"),
    [
        ([], "Bitte mindestens einen Produktnamen auswählen."),
        (["Unknown product"], "Keine Datensätze für die ausgewählten Produkte"),
    ],
)
def test_run_analysis_pipeline_rejects_missing_product_selection(
    selected_products: list[str], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        run_analysis_pipeline(
            _reference_orders(),
            selected_products=selected_products,
            today=date(2026, 6, 18),
        )
