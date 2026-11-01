"""Darstellung des Themes mit konfigurierten Farben (Spezifikationsschritt 7)."""

from pathlib import Path

import streamlit as st

from config import (
    COLOR_BACKGROUND,
    COLOR_BORDER,
    COLOR_CRITICAL,
    COLOR_CRITICAL_BACKGROUND,
    COLOR_HEADER,
    COLOR_INFO,
    COLOR_INFO_BACKGROUND,
    COLOR_INPUT_BORDER,
    COLOR_MUTED,
    COLOR_ON_HEADER,
    COLOR_PRIMARY,
    COLOR_SUCCESS,
    COLOR_SUCCESS_BACKGROUND,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_TREND_WINDOW,
    COLOR_WARNING,
    COLOR_WARNING_BACKGROUND,
)


def apply_theme() -> None:
    """Lädt lokale Styles und stellt die zentral konfigurierten Farben bereit."""
    # Nur Konfigurationskonstanten interpolieren, damit Upload-Daten das CSS nicht steuern.
    variables = (
        ":root {\n"
        f"    --app-background: {COLOR_BACKGROUND};\n"
        f"    --app-surface: {COLOR_SURFACE};\n"
        f"    --app-on-header: {COLOR_ON_HEADER};\n"
        f"    --app-border: {COLOR_BORDER};\n"
        f"    --app-input-border: {COLOR_INPUT_BORDER};\n"
        f"    --app-text: {COLOR_TEXT};\n"
        f"    --app-muted: {COLOR_MUTED};\n"
        f"    --app-primary: {COLOR_PRIMARY};\n"
        f"    --app-header: {COLOR_HEADER};\n"
        f"    --app-success: {COLOR_SUCCESS};\n"
        f"    --app-warning: {COLOR_WARNING};\n"
        f"    --app-critical: {COLOR_CRITICAL};\n"
        f"    --app-info: {COLOR_INFO};\n"
        f"    --app-trend-window: {COLOR_TREND_WINDOW};\n"
        f"    --app-success-background: {COLOR_SUCCESS_BACKGROUND};\n"
        f"    --app-warning-background: {COLOR_WARNING_BACKGROUND};\n"
        f"    --app-critical-background: {COLOR_CRITICAL_BACKGROUND};\n"
        f"    --app-info-background: {COLOR_INFO_BACKGROUND};\n"
        "}\n"
    )
    stylesheet = Path(__file__).with_name("theme.css").read_text(encoding="utf-8")
    st.html(f"<style>\n{variables}{stylesheet}\n</style>")
