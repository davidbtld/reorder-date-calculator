"""Tests zur Positionsbereinigung gemäß Spezifikationsschritt 4."""

import pandas as pd

from core.cleaning import clean_order_lines


def test_clean_order_lines_keeps_positive_numeric_quantities() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-001", "#SYNTH-002"],
            "Lineitem quantity": [2, 1],
            "Lineitem name": ["Fictional bottle", "Fictional mug"],
        }
    )

    cleaned, returns, invalid_quantities = clean_order_lines(orders)

    assert cleaned["Name"].tolist() == ["#SYNTH-001", "#SYNTH-002"]
    assert cleaned["Lineitem quantity"].tolist() == [2, 1]
    assert returns == 0
    assert invalid_quantities == 0


def test_clean_order_lines_excludes_and_counts_negative_quantities() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-003", "#SYNTH-004"],
            "Lineitem quantity": [2, -1],
            "Lineitem name": ["Fictional bowl", "Fictional bowl"],
        }
    )

    cleaned, returns, invalid_quantities = clean_order_lines(orders)

    assert cleaned["Name"].tolist() == ["#SYNTH-003"]
    assert returns == 1
    assert invalid_quantities == 0


def test_clean_order_lines_discards_and_counts_zero_quantity() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-005", "#SYNTH-006"],
            "Lineitem quantity": [0, 1],
            "Lineitem name": ["Fictional cup", "Fictional cup"],
        }
    )

    cleaned, returns, invalid_quantities = clean_order_lines(orders)

    assert cleaned["Name"].tolist() == ["#SYNTH-006"]
    assert returns == 0
    assert invalid_quantities == 1


def test_clean_order_lines_discards_and_counts_text_quantity() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-007", "#SYNTH-008"],
            "Lineitem quantity": ["many", "2"],
            "Lineitem name": ["Fictional tray", "Fictional tray"],
        }
    )

    cleaned, returns, invalid_quantities = clean_order_lines(orders)

    assert cleaned["Name"].tolist() == ["#SYNTH-008"]
    assert returns == 0
    assert invalid_quantities == 1


def test_clean_order_lines_converts_text_number_to_numeric_quantity() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-009"],
            "Lineitem quantity": ["3"],
            "Lineitem name": ["Fictional pitcher"],
        }
    )

    cleaned, returns, invalid_quantities = clean_order_lines(orders)

    assert cleaned["Lineitem quantity"].tolist() == [3]
    assert pd.api.types.is_numeric_dtype(cleaned["Lineitem quantity"])
    assert returns == 0
    assert invalid_quantities == 0


def test_clean_order_lines_returns_empty_input_unchanged() -> None:
    orders = pd.DataFrame(
        columns=["Name", "Lineitem quantity", "Lineitem name"]
    )

    cleaned, returns, invalid_quantities = clean_order_lines(orders)

    assert cleaned.empty
    assert cleaned.columns.tolist() == orders.columns.tolist()
    assert returns == 0
    assert invalid_quantities == 0


def test_clean_order_lines_counts_multiple_quantity_error_types() -> None:
    orders = pd.DataFrame(
        {
            "Name": [
                "#SYNTH-010",
                "#SYNTH-011",
                "#SYNTH-012",
                "#SYNTH-013",
                "#SYNTH-014",
            ],
            "Lineitem quantity": [2, -1, 0, "unknown", "4"],
            "Lineitem name": ["Fictional jar"] * 5,
        }
    )

    cleaned, returns, invalid_quantities = clean_order_lines(orders)

    assert cleaned["Name"].tolist() == ["#SYNTH-010", "#SYNTH-014"]
    assert cleaned["Lineitem quantity"].tolist() == [2, 4]
    assert returns == 1
    assert invalid_quantities == 2
