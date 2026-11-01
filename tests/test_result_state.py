"""Tests der Sichtbarkeit von Ergebniskacheln gemäß Spezifikationsschritt 7."""

import pytest

from ui.result_state import ResultDisplayState, get_result_display_state


@pytest.mark.parametrize(
    ("inventory", "lead_time_days", "expected"),
    [
        (
            None,
            None,
            ResultDisplayState(
                show_reorder_point=False,
                show_main_card=False,
                show_missing_inputs_notice=True,
            ),
        ),
        (
            12,
            None,
            ResultDisplayState(
                show_reorder_point=False,
                show_main_card=False,
                show_missing_inputs_notice=True,
            ),
        ),
        (
            None,
            5,
            ResultDisplayState(
                show_reorder_point=True,
                show_main_card=False,
                show_missing_inputs_notice=True,
            ),
        ),
        (
            0,
            5,
            ResultDisplayState(
                show_reorder_point=True,
                show_main_card=True,
                show_missing_inputs_notice=False,
            ),
        ),
        (
            10,
            0,
            ResultDisplayState(
                show_reorder_point=True,
                show_main_card=True,
                show_missing_inputs_notice=False,
            ),
        ),
    ],
)
def test_result_visibility_tracks_required_inputs(
    inventory: int | None,
    lead_time_days: int | None,
    expected: ResultDisplayState,
) -> None:
    assert get_result_display_state(inventory, lead_time_days) == expected
