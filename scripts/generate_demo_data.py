"""Erzeugt synthetische Demo-Bestelldaten für die Spezifikationsschritte 1 bis 7."""

import argparse
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

SEED = 842_617
DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "sample_data"
DEFAULT_OUTPUT_PATH = DATA_DIRECTORY / "demo_bestellungen.csv"

PRIMARY_PRODUCTS = (
    "Produkt A | Variante 1",
    "Produkt A | Variante 2",
    "Produkt A | Variante 3",
    "Produkt A | Variante 4",
)
OTHER_PRODUCTS = (
    "Produkt B | Variante 1",
    "Produkt C | Variante 1",
    "Produkt D | Variante 1",
)
CSV_COLUMNS = (
    "Name",
    "Email",
    "Paid at",
    "Financial Status",
    "Lineitem quantity",
    "Lineitem name",
)


def _format_paid_at(value: datetime, include_timezone: bool) -> str:
    formatted = value.strftime("%Y-%m-%d %H:%M:%S")
    return f"{formatted} +0200" if include_timezone else formatted


def generate_demo_rows(end_date: date) -> list[dict[str, str | int]]:
    """Erzeugt deterministische, synthetische Bestellpositionen bis einschließlich ``end_date``."""
    if isinstance(end_date, datetime):
        raise ValueError("Das Enddatum muss ein Datum ohne Uhrzeit sein.")

    rng = random.Random(SEED)
    faker = Faker()
    faker.seed_instance(SEED)
    start_date = end_date - timedelta(days=243)
    orders: list[dict[str, object]] = []

    week_start = start_date
    week_index = 0
    while week_start <= end_date:
        week_end = min(week_start + timedelta(days=6), end_date)
        days_in_week = (week_end - week_start).days + 1
        order_count = max(
            4,
            round(7 + week_index * 0.17) + rng.randint(-2, 2),
        )
        for _ in range(order_count):
            order_date = week_start + timedelta(days=rng.randrange(days_in_week))
            primary_product = rng.choice(PRIMARY_PRODUCTS)
            quantity = rng.choices((1, 2, 3), weights=(84, 14, 2), k=1)[0]
            items = [(primary_product, quantity)]
            if rng.random() < 0.13:
                extra_product = rng.choice(
                    PRIMARY_PRODUCTS + OTHER_PRODUCTS
                )
                items.append((extra_product, 1))

            orders.append(
                {
                    "sort_date": order_date,
                    "items": items,
                    "status": "paid",
                    "invalid_date": False,
                }
            )
        week_start += timedelta(days=7)
        week_index += 1

    # Ein ungültiger Zeitstempel im Zeitraum prüft den Ausschluss fehlerhafter Bestellungen.
    malformed_date = end_date - timedelta(days=232)
    orders.append(
        {
            "sort_date": malformed_date,
            "items": [(PRIMARY_PRODUCTS[0], 1)],
            "status": "paid",
            "invalid_date": True,
        }
    )
    for offset, quantity, status in (
        (70, -1, "refunded"),
        (25, -2, "partially_refunded"),
        (12, 0, "paid"),
        (42, 20, "paid"),
    ):
        orders.append(
            {
                "sort_date": end_date - timedelta(days=offset),
                "items": [(rng.choice(PRIMARY_PRODUCTS), quantity)],
                "status": status,
                "invalid_date": False,
            }
        )

    orders.sort(key=lambda order: order["sort_date"])
    rows: list[dict[str, str | int]] = []
    for order_number, order in enumerate(orders, start=1001):
        order_date = order["sort_date"]
        assert isinstance(order_date, date)
        email = f"demo{faker.uuid4().replace('-', '')[:12]}@example.com"
        hour = rng.randrange(8, 21)
        paid_at = datetime.combine(
            order_date,
            datetime.min.time().replace(
                hour=hour,
                minute=rng.randrange(60),
                second=rng.randrange(60),
            ),
        )
        date_text = (
            paid_at.strftime("%Y-%m-%d 17:18.21")
            if order["invalid_date"]
            else _format_paid_at(paid_at, include_timezone=order_number % 4 == 0)
        )
        for item_index, (product_name, quantity) in enumerate(order["items"]):
            rows.append(
                {
                    "Name": f"#{order_number}",
                    "Email": email,
                    "Paid at": date_text if item_index == 0 else "",
                    "Financial Status": str(order["status"]),
                    "Lineitem quantity": quantity,
                    "Lineitem name": product_name,
                }
            )
    return rows


def write_demo_data(
    end_date: date | None = None,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    """Schreibt die synthetische CSV-Datei und liefert ihren Pfad zurück."""
    effective_end_date = end_date if end_date is not None else date.today()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(generate_demo_rows(effective_end_date))
    return output_path


def _parse_end_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Das Enddatum muss im Format YYYY-MM-DD angegeben werden."
        ) from error


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Erzeugt einen vollständig synthetischen Shopify-Bestellexport."
    )
    parser.add_argument(
        "--end-date",
        type=_parse_end_date,
        default=date.today(),
        help="Enddatum im Format YYYY-MM-DD (Standard: heutiges Datum).",
    )
    args = parser.parse_args()
    output_path = write_demo_data(end_date=args.end_date)
    print(f"Synthetische Demo-Daten geschrieben: {output_path}")


if __name__ == "__main__":
    main()
