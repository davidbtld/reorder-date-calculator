"""Tests der Eingabegrenzen für Lagerbestand und Lieferzeit."""

from unittest.mock import Mock

import streamlit as st

from config import MAX_INVENTORY, MAX_LEAD_TIME_DAYS
from ui.inputs import render_parameters


class _Column:
    def __enter__(self) -> "_Column":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_render_parameters_applies_configured_input_maxima(monkeypatch) -> None:
    number_input = Mock(side_effect=[MAX_INVENTORY, MAX_LEAD_TIME_DAYS])
    monkeypatch.setattr(st, "number_input", number_input)

    result = render_parameters(
        product_names=[],
        product_column=_Column(),
        inventory_column=_Column(),
        lead_time_column=_Column(),
    )

    assert result == ([], MAX_INVENTORY, MAX_LEAD_TIME_DAYS)
    assert number_input.call_args_list[0].kwargs["max_value"] == MAX_INVENTORY
    assert number_input.call_args_list[1].kwargs["max_value"] == MAX_LEAD_TIME_DAYS
