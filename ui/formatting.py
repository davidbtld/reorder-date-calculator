"""Deutsche Formatierung der Ergebniswerte gemäß Spezifikationsschritt 7."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from config import DATE_DISPLAY_FORMAT


def format_date(value: date) -> str:
    """Formatiert ein Datum als TT.MM.JJJJ."""
    return value.strftime(DATE_DISPLAY_FORMAT)


def format_date_range(start: date, end: date) -> str:
    """Formatiert einen Zeitraum mit kompaktem Startdatum im selben Jahr."""
    if start.year == end.year:
        return f"{start:%d.%m.} – {format_date(end)}"
    return f"{format_date(start)} – {format_date(end)}"


def format_number(
    value: int | float,
    max_decimal_places: int = 2,
    trim_trailing_zeros: bool = True,
) -> str:
    """Formatiert Zahlen mit deutschem Tausender- und Dezimaltrennzeichen."""
    quantum = Decimal(1).scaleb(-max_decimal_places)
    rounded = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    formatted = format(rounded, f",.{max_decimal_places}f")
    integer_part, _, fractional_part = formatted.partition(".")
    integer_part = integer_part.replace(",", ".")
    if trim_trailing_zeros:
        fractional_part = fractional_part.rstrip("0")
    if max_decimal_places == 0 or (trim_trailing_zeros and not fractional_part):
        return integer_part
    return f"{integer_part},{fractional_part}"
