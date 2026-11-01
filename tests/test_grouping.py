"""Tests der Bestellgruppenbildung gemäß Spezifikationsschritt 3."""

from datetime import datetime

import pandas as pd

from core.grouping import group_orders_by_name


def reference_orders() -> pd.DataFrame:
    """Erzeugt die fiktiven Referenzbestellungen aus den Architekturrichtlinien."""
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
            "Lineitem name": ["Synthetic bottle"] * 9,
        }
    )


def test_group_orders_fills_reference_data_and_excludes_invalid_order() -> None:
    grouped, invalid_order_names = group_orders_by_name(reference_orders())

    assert invalid_order_names.tolist() == ["#0999"]
    assert len(grouped) == 7
    assert grouped["Name"].nunique() == 4
    assert grouped["Name"].tolist() == [
        "#1003",
        "#1003",
        "#1003",
        "#1003",
        "#1002",
        "#1001",
        "#1000",
    ]
    assert grouped["Paid at"].tolist() == [
        "2026-06-17 08:37:12",
        "2026-06-17 08:37:12",
        "2026-06-17 08:37:12",
        "2026-06-17 08:37:12",
        "2026-05-25 15:38:36",
        "2026-05-14 21:27:23",
        "2026-04-09 11:57:59",
    ]
    assert grouped["Lineitem quantity"].sum() == 7


def test_group_orders_uses_first_parseable_value_after_invalid_value() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-001", "#SYNTH-001", "#SYNTH-001"],
            "Paid at": [
                "2026-03-10 17:18.21",
                "2026-03-10 17:18:21",
                "2026-03-11 09:00:00",
            ],
            "Lineitem quantity": [1, 1, 1],
            "Lineitem name": ["Synthetic mug"] * 3,
        }
    )

    grouped, invalid_order_names = group_orders_by_name(orders)

    assert invalid_order_names.empty
    assert len(grouped) == 3
    assert grouped["Paid at"].tolist() == ["2026-03-10 17:18:21"] * 3


def test_group_orders_accepts_timestamps_with_and_without_timezone_offset() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-005", "#SYNTH-006"],
            "Paid at": [
                "2026-04-09 11:57:59 +0200",
                "2026-04-09 11:57:59",
            ],
            "Lineitem quantity": [1, 1],
            "Lineitem name": ["Synthetic bowl", "Synthetic tray"],
        }
    )

    grouped, invalid_order_names = group_orders_by_name(orders)

    assert invalid_order_names.empty
    assert grouped["Name"].tolist() == ["#SYNTH-005", "#SYNTH-006"]
    assert grouped["Paid at"].tolist() == [
        "2026-04-09 11:57:59 +0200",
        "2026-04-09 11:57:59",
    ]


def test_group_orders_accepts_excel_datetime_values() -> None:
    excel_datetime = datetime(2026, 4, 9, 11, 57, 59)
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-007"],
            "Paid at": [excel_datetime],
            "Lineitem quantity": [1],
            "Lineitem name": ["Synthetic jar"],
        }
    )

    grouped, invalid_order_names = group_orders_by_name(orders)

    assert invalid_order_names.empty
    assert grouped.loc[0, "Paid at"] == excel_datetime


def test_group_orders_rejects_obviously_invalid_date_text() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-008", "#SYNTH-008"],
            "Paid at": ["not a real date", None],
            "Lineitem quantity": [1, 1],
            "Lineitem name": ["Synthetic lamp", "Synthetic lamp"],
        }
    )

    grouped, invalid_order_names = group_orders_by_name(orders)

    assert grouped.empty
    assert invalid_order_names.tolist() == ["#SYNTH-008"]


def test_group_orders_reports_a_group_without_valid_date_once() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-002", "#SYNTH-002", "#SYNTH-003"],
            "Paid at": ["not-a-date", None, "2026-03-12 10:00:00"],
            "Lineitem quantity": [1, 2, 1],
            "Lineitem name": ["Synthetic cup"] * 3,
        }
    )

    grouped, invalid_order_names = group_orders_by_name(orders)

    assert invalid_order_names.tolist() == ["#SYNTH-002"]
    assert grouped["Name"].tolist() == ["#SYNTH-003"]
    assert grouped["Lineitem quantity"].tolist() == [1]


def test_group_orders_keeps_every_row_without_deduplication() -> None:
    orders = pd.DataFrame(
        {
            "Name": ["#SYNTH-004", "#SYNTH-004"],
            "Paid at": ["2026-03-13 11:00:00", None],
            "Lineitem quantity": [1, 1],
            "Lineitem name": ["Synthetic plate", "Synthetic plate"],
        }
    )

    grouped, invalid_order_names = group_orders_by_name(orders)

    assert invalid_order_names.empty
    assert len(grouped) == 2
    assert grouped["Lineitem name"].tolist() == ["Synthetic plate", "Synthetic plate"]
    assert grouped["Paid at"].tolist() == ["2026-03-13 11:00:00"] * 2


def test_group_orders_returns_empty_input_unchanged() -> None:
    orders = pd.DataFrame(
        columns=["Name", "Paid at", "Lineitem quantity", "Lineitem name"]
    )

    grouped, invalid_order_names = group_orders_by_name(orders)

    assert grouped.empty
    assert grouped.columns.tolist() == orders.columns.tolist()
    assert invalid_order_names.empty
