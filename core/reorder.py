"""Nachbestellempfehlung und Ampelbewertung gemäß Spezifikationsschritt 7."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from fractions import Fraction
from typing import Literal

from config import URGENCY_CRITICAL_DAYS, URGENCY_WARNING_DAYS


ReorderUrgency = Literal["ok", "warning", "critical"]


@dataclass(frozen=True)
class ReorderRecommendation:
    """Typisiertes Ergebnis der Nachbestellempfehlung."""

    reorder_point: float | None
    order_immediately: bool
    days_until_reorder: int | None
    order_date: date | None


def classify_reorder_urgency(
    days_until_reorder: int | None,
    inventory: int,
    reorder_point: float | None,
) -> ReorderUrgency | None:
    """Ordnet Bestand und verbleibende Tage einer Ampelstufe zu."""
    if reorder_point is None:
        return None
    # Ein erreichter Meldebestand hat Vorrang vor den zeitlichen Warnstufen.
    if inventory <= reorder_point:
        return "critical"
    if days_until_reorder is None or days_until_reorder < 0:
        raise ValueError(
            "Für einen Bestand über dem Meldebestand werden gültige "
            "Tage bis zur Bestellung benötigt."
        )
    if days_until_reorder <= URGENCY_CRITICAL_DAYS:
        return "critical"
    if days_until_reorder <= URGENCY_WARNING_DAYS:
        return "warning"
    return "ok"


def _validate_inventory(inventory: int) -> None:
    if isinstance(inventory, bool) or not isinstance(inventory, int) or inventory < 0:
        raise ValueError(
            "Der Lagerbestand muss eine ganze Zahl größer oder gleich 0 sein."
        )


def _validate_lead_time(lead_time_days: int) -> None:
    if (
        isinstance(lead_time_days, bool)
        or not isinstance(lead_time_days, int)
        or lead_time_days < 0
    ):
        raise ValueError(
            "Die Lieferzeit muss eine ganze Zahl größer oder gleich 0 sein."
        )


def _validated_trend_fraction(
    total_quantity: int | float,
    covered_days: int,
) -> Fraction:
    if (
        isinstance(covered_days, bool)
        or not isinstance(covered_days, int)
        or covered_days <= 0
    ):
        raise ValueError("Die abgedeckten Tage müssen eine ganze Zahl größer 0 sein.")
    try:
        exact_quantity = Fraction(str(total_quantity))
    except (TypeError, ValueError, ZeroDivisionError):
        raise ValueError(
            "Der Trend muss eine endliche Zahl größer oder gleich 0 sein."
        ) from None
    if exact_quantity < 0:
        raise ValueError("Der Trend muss eine endliche Zahl größer oder gleich 0 sein.")
    return exact_quantity / covered_days


def calculate_reorder_point(
    total_quantity: int | float,
    covered_days: int,
    lead_time_days: int,
) -> float:
    """Berechnet den Meldebestand gemäß Abschnitt 4 der funktionalen Spezifikation.

    Args:
        total_quantity: Absatzsumme im abgedeckten Zeitraum (>= 0).
        covered_days: Anzahl der abgedeckten Kalendertage (> 0).
        lead_time_days: Lieferzeit in Tagen (>= 0).

    Returns:
        Den Reorder Point in Stück.

    Raises:
        ValueError: Wenn Trend oder Lieferzeit ungültig sind.
    """
    _validate_lead_time(lead_time_days)
    return float(
        _validated_trend_fraction(total_quantity, covered_days) * lead_time_days
    )


def calculate_reorder_recommendation(
    total_quantity: int | float,
    covered_days: int,
    inventory: int,
    lead_time_days: int,
    today: date,
) -> ReorderRecommendation:
    """Ermittelt Meldebestand und spätestes Bestelldatum gemäß Abschnitt 4 und 7.

    Der Lagerbestand ist der Ist-Bestand von heute; Dateiverkäufe werden nicht
    erneut abgezogen. Bei Trend 0 ist keine Reorder-Berechnung möglich.

    Args:
        total_quantity: Exakte Absatzsumme im abgedeckten Zeitraum.
        covered_days: Anzahl der abgedeckten Kalendertage.
        inventory: Physischer Ist-Lagerbestand von heute (Ganzzahl >= 0).
        lead_time_days: Lieferzeit in Tagen (Ganzzahl >= 0).
        today: Referenzdatum; das Systemdatum wird nicht selbst abgefragt.

    Returns:
        Ein ReorderRecommendation mit Meldebestand, Sofort-Kennzeichen und optionalem
        Zeitraum/Bestelldatum. Bei Trend 0 sind alle Berechnungswerte None.

    Raises:
        ValueError: Wenn Lagerbestand, Lieferzeit, Trend oder Referenzdatum
            ungültig sind.
    """
    _validate_inventory(inventory)
    _validate_lead_time(lead_time_days)
    if not isinstance(today, date) or isinstance(today, datetime):
        raise ValueError("Das Referenzdatum 'today' muss ein Datum sein.")
    trend = _validated_trend_fraction(total_quantity, covered_days)
    if trend == 0:
        return ReorderRecommendation(
            reorder_point=None,
            order_immediately=False,
            days_until_reorder=None,
            order_date=None,
        )

    reorder_point_fraction = trend * lead_time_days
    reorder_point = float(reorder_point_fraction)

    if Fraction(inventory) <= reorder_point_fraction:
        return ReorderRecommendation(
            reorder_point=reorder_point,
            order_immediately=True,
            days_until_reorder=None,
            order_date=None,
        )

    days_until_reorder = (Fraction(inventory) - reorder_point_fraction) // trend
    return ReorderRecommendation(
        reorder_point=reorder_point,
        order_immediately=False,
        days_until_reorder=int(days_until_reorder),
        order_date=today + timedelta(days=int(days_until_reorder)),
    )
