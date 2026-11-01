"""Tests zum Einlesen und Prüfen der Dateien gemäß Spezifikationsschritt 1."""

from io import BytesIO
from pathlib import Path
from datetime import datetime

import pandas as pd
import pytest

from data.loader import load_orders


class UploadedFile(BytesIO):
    """Minimales, synthetisches Dateiobjekt wie ein hochgeladener XLSX-Upload."""

    def __init__(self, content: bytes, name: str) -> None:
        super().__init__(content)
        self.name = name


def test_load_orders_reads_csv_path_and_keeps_other_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "fictional_orders.csv"
    csv_path.write_text(
        "Name,Paid at,Lineitem quantity,Lineitem name,Extra field\n"
        "#TEST-001,2026-01-01 12:00:00,2,Fictional bottle,synthetic value\n",
        encoding="utf-8",
    )

    orders = load_orders(csv_path)

    assert orders.loc[0, "Name"] == "#TEST-001"
    assert orders.loc[0, "Lineitem quantity"] == 2
    assert orders.loc[0, "Extra field"] == "synthetic value"


def test_load_orders_reads_xlsx_uploaded_file() -> None:
    fictional_orders = pd.DataFrame(
        {
            "Name": ["#TEST-002"],
            "Paid at": ["2026-01-02 09:30:00"],
            "Lineitem quantity": [1],
            "Lineitem name": ["Fictional mug"],
        }
    )
    excel_content = BytesIO()
    fictional_orders.to_excel(excel_content, index=False, engine="openpyxl")
    upload = UploadedFile(excel_content.getvalue(), "fictional_orders.xlsx")

    orders = load_orders(upload)

    assert orders.loc[0, "Name"] == "#TEST-002"
    assert orders.loc[0, "Lineitem name"] == "Fictional mug"


def test_load_orders_preserves_excel_datetime_cell() -> None:
    excel_datetime = datetime(2026, 4, 9, 11, 57, 59)
    fictional_orders = pd.DataFrame(
        {
            "Name": ["#TEST-004"],
            "Paid at": [excel_datetime],
            "Lineitem quantity": [1],
            "Lineitem name": ["Fictional bowl"],
        }
    )
    excel_content = BytesIO()
    fictional_orders.to_excel(excel_content, index=False, engine="openpyxl")
    upload = UploadedFile(excel_content.getvalue(), "fictional_datetime_orders.xlsx")

    orders = load_orders(upload)

    assert orders.loc[0, "Paid at"] == pd.Timestamp(excel_datetime)


def test_load_orders_reports_missing_required_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing_column.csv"
    csv_path.write_text(
        "Name,Paid at,Lineitem name\n#TEST-003,2026-01-03,Fictional cup\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Lineitem quantity"):
        load_orders(csv_path)


def test_load_orders_reports_empty_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    csv_path.write_bytes(b"")

    with pytest.raises(ValueError, match="leer"):
        load_orders(csv_path)


def test_load_orders_rejects_unsupported_file_format(tmp_path: Path) -> None:
    unsupported_path = tmp_path / "fictional_document.pdf"
    unsupported_path.write_bytes(b"synthetic test content")

    with pytest.raises(ValueError, match="CSV- oder Excel-Datei"):
        load_orders(unsupported_path)


def test_load_orders_reports_corrupted_xlsx(tmp_path: Path) -> None:
    corrupted_path = tmp_path / "corrupted.xlsx"
    corrupted_path.write_bytes(b"synthetic invalid workbook content")

    with pytest.raises(ValueError, match="beschädigt"):
        load_orders(corrupted_path)
