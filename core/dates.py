"""Gemeinsame Kalenderdatums-Konvertierung für Spezifikationsschritte 3, 5 und 6."""

from datetime import date, datetime

import pandas as pd


def calendar_date(value: object) -> date | None:
    """Liefert das Kalenderdatum eines gültigen Zahlungsdatums."""
    if not isinstance(value, (str, date, datetime)):
        return None

    parsed_value = pd.to_datetime(value, format="ISO8601", errors="coerce")
    if pd.isna(parsed_value):
        return None

    return parsed_value.date()
