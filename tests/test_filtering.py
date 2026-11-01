"""Tests der Produktauswahl gemäß Spezifikationsschritt 2."""

import pandas as pd

from core.filtering import (
    filter_by_selected_products,
    get_distinct_product_names,
)


def test_get_distinct_product_names_returns_sorted_unique_trimmed_names() -> None:
    orders = pd.DataFrame(
        {
            "Lineitem name": [
                "  Fictional bottle ",
                "Fictional mug",
                "Fictional bottle",
                None,
            ]
        }
    )

    assert get_distinct_product_names(orders) == [
        "Fictional bottle",
        "Fictional mug",
    ]


def test_filter_by_selected_products_matches_exact_product_name() -> None:
    orders = pd.DataFrame(
        {
            "Lineitem name": [
                "Fictional bottle",
                "Fictional bottle XL",
                "Fictional mug",
            ],
            "quantity": [1, 2, 3],
        }
    )

    filtered = filter_by_selected_products(orders, ["Fictional bottle"])

    assert filtered["quantity"].tolist() == [1]
    assert filtered["Lineitem name"].tolist() == ["Fictional bottle"]


def test_filter_by_selected_products_keeps_multiple_selected_products() -> None:
    orders = pd.DataFrame(
        {
            "Lineitem name": [
                "Fictional bottle",
                "Fictional mug",
                "Fictional cup",
            ]
        }
    )

    filtered = filter_by_selected_products(
        orders, ["Fictional bottle", "Fictional cup"]
    )

    assert filtered["Lineitem name"].tolist() == [
        "Fictional bottle",
        "Fictional cup",
    ]


def test_filter_by_selected_products_trims_names_before_exact_comparison() -> None:
    orders = pd.DataFrame(
        {"Lineitem name": [" Fictional bottle", "Fictional bottle ", "Fictional mug"]}
    )

    filtered = filter_by_selected_products(orders, [" Fictional bottle "])

    assert filtered["Lineitem name"].tolist() == [
        " Fictional bottle",
        "Fictional bottle ",
    ]


def test_filter_by_selected_products_returns_no_rows_for_empty_selection() -> None:
    orders = pd.DataFrame({"Lineitem name": ["Fictional bottle"]})

    filtered = filter_by_selected_products(orders, [])

    assert filtered.empty
    assert list(filtered.columns) == ["Lineitem name"]


def test_filter_by_selected_products_returns_no_rows_for_missing_product() -> None:
    orders = pd.DataFrame({"Lineitem name": ["Fictional bottle"]})

    filtered = filter_by_selected_products(orders, ["Fictional pitcher"])

    assert filtered.empty
