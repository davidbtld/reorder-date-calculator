"""Sichtbarkeitszustand der Ergebniskacheln gemäß Spezifikationsschritt 7."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultDisplayState:
    """Bestimmt, welche Empfehlungskacheln zu den Eingaben angezeigt werden."""

    show_reorder_point: bool
    show_main_card: bool
    show_missing_inputs_notice: bool


def get_result_display_state(
    inventory: int | None,
    lead_time_days: int | None,
) -> ResultDisplayState:
    """Leitet die Sichtbarkeit aus vorhandenen Pflichtangaben ab."""
    show_main_card = inventory is not None and lead_time_days is not None
    return ResultDisplayState(
        show_reorder_point=lead_time_days is not None,
        show_main_card=show_main_card,
        show_missing_inputs_notice=not show_main_card,
    )
