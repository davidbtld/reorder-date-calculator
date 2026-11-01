"""Zentrale Anwendungswerte mit Einheiten gemäß funktionaler Spezifikation."""

import os

# Trend- und Abdeckungsprüfung (Schritte 5–6)
TREND_WINDOW_DAYS = 90  # Tage

# Diagramm (Spezifikation 5.1)
CHART_MONTHS = 6  # Monate
APP_TITLE = "Lageranalyse"

# Demo-Modus (nur gehostete Demo): zeigt Hinweis "keine echten Daten hochladen"
DEMO_MODE = os.environ.get("LAGERANALYSE_DEMO") == "1"

# Pflichtspalten (Schritt 1)
REQUIRED_COLUMNS = ["Name", "Paid at", "Lineitem quantity", "Lineitem name"]

# Dringlichkeit der Hauptkachel (Spezifikation Schritt 7 / 5.1)
URGENCY_WARNING_DAYS = 7  # Tage bis zur Bestellung
URGENCY_CRITICAL_DAYS = 2  # Tage bis zur Bestellung

# Darstellung im Geschäftsstil; Farben als Hexadezimalwerte
COLOR_PRIMARY = "#0a6ed1"
COLOR_HEADER = "#34495e"
COLOR_BACKGROUND = "#f3f4f5"
COLOR_SURFACE = "#ffffff"
COLOR_ON_HEADER = "#ffffff"
COLOR_BORDER = "#d9dde1"
COLOR_INPUT_BORDER = "#89919a"
COLOR_GRID = "#e6e8eb"
COLOR_TEXT = "#32363a"
COLOR_MUTED = "#6a6d70"
COLOR_SUCCESS = "#188918"
COLOR_WARNING = "#e9730c"
COLOR_CRITICAL = "#bb0000"
COLOR_INFO = "#0a6ed1"
COLOR_TREND_WINDOW = "#dceaf8"
COLOR_SUCCESS_BACKGROUND = "#e5f5e5"
COLOR_WARNING_BACKGROUND = "#fff3e5"
COLOR_CRITICAL_BACKGROUND = "#ffeaf0"
COLOR_INFO_BACKGROUND = "#eaf3fc"

# Anzeigeformat für Kalenderdaten
DATE_DISPLAY_FORMAT = "%d.%m.%Y"  # Europäische Schreibweise, z. B. 07.10.2026
