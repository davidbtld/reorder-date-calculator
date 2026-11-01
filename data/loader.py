"""Laden und Prüfen von Bestelldateien gemäß Spezifikationsschritt 1."""

from pathlib import Path
from typing import BinaryIO
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

import pandas as pd
from openpyxl.utils.exceptions import InvalidFileException

from config import REQUIRED_COLUMNS


def load_orders(source: str | Path | BinaryIO) -> pd.DataFrame:
    """Liest eine CSV- oder XLSX-Datei ein und prüft die Pflichtspalten.

    Entspricht Schritt 1 der funktionalen Spezifikation sowie der
    Schnittstelle der Datenschicht aus Abschnitt 5 der Architekturrichtlinien.

    Args:
        source: Dateipfad oder benanntes, binäres Dateiobjekt wie ein Upload.

    Returns:
        Die eingelesenen Bestellzeilen als DataFrame.

    Raises:
        ValueError: Wenn Format, Inhalt oder Pflichtspalten ungültig sind.
        FileNotFoundError: Wenn der angegebene Dateipfad nicht existiert.
    """
    if isinstance(source, (str, Path)):
        file_name = str(source)
    else:
        file_name = getattr(source, "name", "")

    suffix = Path(file_name).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise ValueError(
            "Nicht unterstütztes Dateiformat. Bitte eine CSV- oder "
            "Excel-Datei (.xlsx) verwenden."
        )

    if not isinstance(source, (str, Path)):
        # Upload-Streams können beim Ermitteln des Dateinamens bereits gelesen worden sein.
        source.seek(0)

    try:
        if suffix == ".csv":
            orders = pd.read_csv(source)
        else:
            orders = pd.read_excel(source, engine="openpyxl")
    except pd.errors.EmptyDataError as error:
        raise ValueError("Die Datei ist leer oder enthält keine Daten.") from error
    except pd.errors.ParserError as error:
        raise ValueError("Die CSV-Datei ist beschädigt oder kann nicht gelesen werden.") from error
    except UnicodeDecodeError as error:
        raise ValueError("Die CSV-Datei verwendet eine nicht unterstützte Textkodierung.") from error
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Die Datei wurde nicht gefunden: {file_name}") from error
    # Technische Parserfehler werden vereinheitlicht, damit die Oberfläche sie verständlich anzeigen kann.
    except (BadZipFile, InvalidFileException, OSError, ParseError, ValueError) as error:
        raise ValueError("Die Datei ist beschädigt oder kann nicht gelesen werden.") from error

    if orders.empty or len(orders.columns) == 0:
        raise ValueError("Die Datei ist leer oder enthält keine Daten.")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in orders.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"Die Datei enthält nicht alle erforderlichen Spalten. "
            f"Es fehlen: {missing}."
        )

    return orders
