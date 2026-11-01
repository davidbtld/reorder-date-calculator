"""Tests synthetischer Beispieldaten für Spezifikationsschritte 1 bis 7."""

from datetime import date
from pathlib import Path

import pandas as pd

from core.pipeline import run_analysis_pipeline
from data.loader import load_orders
from scripts.generate_demo_data import write_demo_data

END_DATE = date(2026, 10, 28)
DEMO_FILE = Path(__file__).resolve().parents[1] / "sample_data" / "demo_bestellungen.csv"


def test_generated_demo_csv_loads_and_runs_through_pipeline(tmp_path: Path) -> None:
    generated_file = write_demo_data(
        end_date=END_DATE,
        output_path=tmp_path / "demo_bestellungen.csv",
    )

    assert generated_file.read_bytes() == DEMO_FILE.read_bytes()
    orders = load_orders(generated_file)
    primary_products = sorted(
        product
        for product in orders["Lineitem name"].unique()
        if product.startswith("Produkt A |")
    )

    result = run_analysis_pipeline(
        orders,
        selected_products=primary_products,
        today=END_DATE,
    )

    assert result.excluded_orders == 1
    assert result.return_lines == 2
    assert result.invalid_quantity_lines == 1
    assert result.considered_rows > 0
    assert result.considered_orders > 0
    assert result.trend.total_quantity > 0
    assert result.weekly_sales["quantity"].sum() > 0
    assert result.weekly_sales["quantity"].tail(4).sum() > result.weekly_sales[
        "quantity"
    ].head(4).sum()


def test_demo_csv_contains_required_synthetic_shopify_edge_cases() -> None:
    orders = load_orders(DEMO_FILE)

    assert orders.columns.tolist() == [
        "Name",
        "Email",
        "Paid at",
        "Financial Status",
        "Lineitem quantity",
        "Lineitem name",
    ]
    assert orders["Email"].str.fullmatch(r"[^@\s]+@example\.com").all()
    assert orders["Name"].str.fullmatch(r"#\d+").all()
    assert set(orders["Lineitem name"]) == {
        "Produkt A | Variante 1",
        "Produkt A | Variante 2",
        "Produkt A | Variante 3",
        "Produkt A | Variante 4",
        "Produkt B | Variante 1",
        "Produkt C | Variante 1",
        "Produkt D | Variante 1",
    }
    assert (orders["Lineitem quantity"] == 20).sum() == 1
    assert (orders["Lineitem quantity"] == 0).sum() == 1
    assert (orders["Lineitem quantity"] < 0).sum() == 2
    assert (orders["Paid at"] == "2026-03-10 17:18.21").sum() == 1
    assert orders["Paid at"].str.contains(r" \+0200$").any()

    multi_line_orders = orders.groupby("Name", sort=False)
    assert any(
        len(group) > 1
        and bool(group.iloc[0]["Paid at"])
        and (
            group.iloc[1:]["Paid at"].isna()
            | group.iloc[1:]["Paid at"].eq("")
        ).all()
        for _, group in multi_line_orders
    )

    nonempty_paid_at = orders.loc[
        orders["Paid at"].notna() & orders["Paid at"].ne(""),
        "Paid at",
    ]
    parsed_dates = pd.to_datetime(
        nonempty_paid_at,
        format="ISO8601",
        errors="coerce",
        utc=True,
    )
    assert parsed_dates.isna().sum() == 1
