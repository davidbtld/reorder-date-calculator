# Architektur- und Code-Richtlinien: Lager- und Trendanalyse-Tool

**Ergänzung zur funktionalen Spezifikation** (`Funktionale_Spezifikation_Lageranalyse_Tool.md`). Die Spezifikation legt fest, *was* berechnet wird. Dieses Dokument beschreibt, *wie* der Code aufgebaut ist und warum, damit Anpassungen und Erweiterungen möglich sind, ohne bestehende Funktionen zu gefährden.

**Technische Grunddaten**

- **Sprache:** Python 3.13 (entwickelt und getestet mit dieser Version)
- **Oberfläche:** Streamlit, läuft lokal auf `localhost`
- **Bibliotheken:** pandas, openpyxl, altair, streamlit (siehe `requirements.txt`)
- **Tests:** pytest (siehe `requirements-dev.txt`), 95 Tests
- **Versionierung:** Git

---

## 1. Leitprinzip: Schichtenarchitektur

Der Code ist in Schichten gegliedert. Jede Schicht kennt nur die Schichten unter sich und kommuniziert über typisierte Funktionssignaturen, nie über globale Variablen oder versteckte Seiteneffekte.

```
┌─────────────────────────────────────────────┐
│  Presentation (Streamlit)        ui/         │
│  Eingabefelder, Kacheln, Diagramm, Theme     │
├─────────────────────────────────────────────┤
│  Business-Logik                  core/       │
│  Gruppierung, Bereinigung, Trend, Meldebestand│
├─────────────────────────────────────────────┤
│  Daten                           data/       │
│  Datei einlesen, Pflichtspalten prüfen       │
├─────────────────────────────────────────────┤
│  Konfiguration                   config.py   │
│  Konstanten, Schwellenwerte, Farben          │
└─────────────────────────────────────────────┘
```

**Kernregel:** `core/` darf nie wissen, dass es Streamlit, eine Datei oder einen Upload-Button gibt. Die Schicht bekommt saubere Daten und liefert Zahlen zurück. Dadurch ist sie ohne Browser testbar und unabhängig von der Oberfläche.

---

## 2. Projektstruktur

```
├── app.py                 Streamlit-Einstiegspunkt (nur Verdrahtung, keine Rechenlogik)
├── config.py              Zentrale Konstanten
├── requirements.txt       Laufzeit-Abhängigkeiten
├── requirements-dev.txt   Entwicklung und Tests (pytest, Faker)
├── .streamlit/config.toml Theme und Servereinstellungen
├── data/
│   └── loader.py          Schritt 1: Datei einlesen, Pflichtspalten prüfen
├── core/
│   ├── filtering.py       Schritt 2: Produktnamen ermitteln, Produktfilter
│   ├── grouping.py        Schritt 3: Gruppierung nach Bestellnummer, Forward-Fill
│   ├── cleaning.py        Schritt 4: Zeilenbereinigung
│   ├── dates.py           Gemeinsame Datumskonvertierung
│   ├── trend.py           Schritte 5–6: Abdeckungsprüfung, Trend
│   ├── reorder.py         Schritt 7: Meldebestand, Bestelldatum, Dringlichkeit
│   ├── weekly_sales.py    Wochenaggregation für das Diagramm
│   └── pipeline.py        Führt die Schritte 2–6 in fester Reihenfolge aus
├── ui/
│   ├── inputs.py          Upload, Produktauswahl, Lagerbestand, Lieferzeit
│   ├── results.py         Kacheln, Hinweisleisten, Handlungsempfehlung
│   ├── result_state.py    Welche Kacheln bei welchen Eingaben sichtbar sind
│   ├── chart.py           Wochendiagramm
│   ├── formatting.py      Datums- und Zahlenformate (deutsch)
│   ├── theme.py           Lädt das Styling
│   └── theme.css          Styling (Farben kommen aus config.py)
├── scripts/
│   └── generate_demo_data.py   Erzeugt die synthetischen Demo-Daten
├── sample_data/
│   └── demo_bestellungen.csv   Synthetische Beispieldaten
├── tests/                 Ein Testmodul pro Modul
└── docs/                  Spezifikation, diese Richtlinien, UI-Skizze, Screenshots
```

Jede Datei in `core/` entspricht einem Schritt der Spezifikation. Wer die Spezifikation gelesen hat, findet sich im Code sofort zurecht: Schritt 3 (Gruppierung, Forward-Fill) liegt in `core/grouping.py`. Dokumentation und Code verwenden dieselbe Sprache.

---

## 3. Zentrale Konfiguration

Werte, die sich später ändern könnten, stehen ausschließlich in `config.py` und nirgends sonst im Code (keine „Magic Numbers“):

- `TREND_WINDOW_DAYS = 90`: Länge des Trendfensters
- `CHART_MONTHS = 6`: Zeitraum des Diagramms
- `REQUIRED_COLUMNS`: die vier Pflichtspalten
- `URGENCY_WARNING_DAYS = 7`, `URGENCY_CRITICAL_DAYS = 2`: Schwellen der Ampel
- `COLOR_*`: alle Farben der Oberfläche
- `DATE_DISPLAY_FORMAT = "%d.%m.%Y"`: Datumsformat der Ausgabe
- `DEMO_MODE`: über die Umgebungsvariable `LAGERANALYSE_DEMO=1` schaltbar, zeigt einen Hinweis, keine echten Daten hochzuladen

Der Produktname steht bewusst **nicht** in der Konfiguration. Der Nutzer wählt ihn zur Laufzeit aus den Werten, die tatsächlich in der Datei vorkommen. Dadurch funktioniert das Tool für jeden Shopify-Export ohne Codeänderung.

---

## 4. Schnittstellen und Code-Stil

- **Benennung:** Funktions- und Variablennamen auf Englisch, Kommentare und Docstrings auf Deutsch (durchgängig).
- **Typen:** Alle Funktionssignaturen in `core/` und `data/` haben Type Hints.
- **Docstrings:** Die öffentlichen Funktionen in `core/`, `data/` und `ui/` haben einen Docstring. Größere Funktionen beschreiben zusätzlich Argumente, Rückgabe und mögliche Fehler und verweisen auf den passenden Abschnitt der Spezifikation.
- **Ergebnisobjekte:** Ergebnisse werden als unveränderliche `dataclass`-Objekte geliefert (`TrendResult`, `PipelineResult`, `ReorderRecommendation`) statt als lose Tupel.
- **Kein Systemdatum in `core/`:** Funktionen erhalten „heute“ als Parameter (`today: date`). Nur so sind sie deterministisch testbar. Die Oberfläche übergibt `date.today()`.
- **Keine Berechnung in `ui/`:** Die Streamlit-Dateien rufen Funktionen aus `core/` auf und stellen Ergebnisse dar.
- **Eine Funktion, eine Aufgabe:** Funktionen, die mehr als einen Schritt der Spezifikation erledigen würden, werden aufgeteilt.

---

## 5. Erweiterbarkeit

| Mögliche Erweiterung | Vorkehrung im Code |
|---|---|
| **Sicherheitsbestand** (bewusst nicht enthalten) | `calculate_reorder_point()` und `calculate_reorder_recommendation()` sind isoliert; ein zusätzlicher Parameter ist eine kleine, lokale Änderung. |
| **Mehrere Produkte mit eigenen Parametern** | Der Produktname ist eine Laufzeit-Auswahl. Ein Dashboard müsste die Kernfunktionen nur in einer Schleife aufrufen. |
| **Live-Anbindung statt Datei-Upload** | `data/loader.py` bietet eine einzige Schnittstelle `load_orders(source)`. Der Rest ändert sich nicht. |
| **`Financial Status` als Gültigkeitskriterium** | `core/cleaning.py` ist ein eigenständiger Prüfschritt; eine zusätzliche Regel ist eine zusätzliche Funktion. |
| **Gewichteter Trend** (z. B. exponentielle Glättung) | Die Trendberechnung liegt gekapselt in `core/trend.py`. |

**Geplant:** eine als Programm installierbare Desktop-Version für Windows und macOS sowie automatische Testläufe über GitHub Actions.

---

## 6. Exakte Berechnung

Trend und Meldebestand werden in `core/reorder.py` mit rationalen Zahlen (`fractions.Fraction`) aus Absatzsumme und abgedeckten Tagen berechnet, nicht aus einem bereits gerundeten Dezimalwert. Hintergrund: Ein Trend wie 200 ÷ 90 = 2,2222… lässt sich als Dezimalzahl nicht exakt speichern. Rechnet man damit weiter, kann ein Ergebnis, das mathematisch genau 33 Tage ist, als 32,999… herauskommen und beim Abrunden einen Tag zu früh liegen. Mit Brüchen entfällt dieses Problem. Die Dezimalwerte für die Anzeige entstehen erst am Ende. Eine Regressionsprüfung dafür steht in `tests/test_reorder.py`.

---

## 7. Zustandsverwaltung in Streamlit

Streamlit führt bei jeder Eingabe das ganze Skript neu aus. Damit die Datei nicht bei jeder Änderung von Lagerbestand oder Lieferzeit neu verarbeitet wird, gilt:

- Die teuren, nur von der Datei abhängigen Schritte (Einlesen, Produktfilter, Forward-Fill, Bereinigung, Trend) sind mit `st.cache_data` zwischengespeichert. Der Cache-Schlüssel besteht aus dem Dateiinhalt, der Produktauswahl und dem Datum.
- Nur der günstige letzte Schritt (Meldebestand und Bestelldatum aus Lagerbestand und Lieferzeit) läuft bei jeder Eingabe neu. So reagiert die Anzeige sofort.

---

## 8. Testkonzept

- **Framework:** pytest. Es gibt ein Testmodul pro Modul in `tests/`.
- **Grundsatz:** Jede Funktion in `core/` hat mindestens einen Normalfall- und einen Grenzfalltest. Jede Fehlerbehandlung aus Abschnitt 7 der Spezifikation wird zu einem Testfall.
- **Wichtige Fälle:**
  - Forward-Fill über mehrere Zeilen derselben Bestellung (`test_grouping.py`)
  - nicht lesbares Datum innerhalb einer Bestellgruppe
  - Trend = 0 (keine Division durch null)
  - alle Verkäufe an einem Tag ergeben einen abgedeckten Tag
  - Lagerbestand = 0 und Lagerbestand ≤ Meldebestand (Sofort-Bestellen)
  - Ampelgrenzen bei 0, 2, 3, 7 und 8 Tagen
  - exakte Ergebnisse, die genau auf eine ganze Zahl fallen (z. B. 200 Stück in 90 Tagen, Bestand 120, Lieferzeit 21 → 33 Tage)
- **Referenz-Testdaten** (vollständig fiktiv, an die Struktur echter Shopify-Exporte angelehnt, nur die relevanten Spalten; jede Zeile hat `Lineitem quantity` = 1 und `Lineitem name` = „Produkt A | Variante 1“):

| Zeile | Name | Paid at |
|---|---|---|
| 1 | #1003 | 2026-06-17 08:37:12 |
| 2–4 | #1003 | (leer) |
| 5 | #1002 | 2026-05-25 15:38:36 |
| 6 | #1001 | 2026-05-14 21:27:23 |
| 7 | #1000 | 2026-04-09 11:57:59 |
| 8 | #0999 | 2026-03-10 17:18.21 (ungültiges Format: Punkt statt Doppelpunkt) |
| 9 | #0999 | (leer) |

Erwartetes Ergebnis nach den Schritten 1–4: 4 gültige Bestellungen (#1003 bis #1000), 7 Einheiten, 1 ausgeschlossene Bestellung (#0999), ältestes Datum 2026-04-09, jüngstes Datum 2026-06-17. Tests mit zeitabhängigem Ergebnis übergeben ein festes „heute“ (z. B. 2026-06-18).

---

## 9. Fehlerbehandlung

- Fachliche Fehler (fehlende Spalten, keine Produktauswahl, Trend = 0, ungültige Eingaben) sind in Abschnitt 7 der Spezifikation beschrieben und werden in der Oberfläche als verständliche Meldung angezeigt.
- Technische Fehler (falscher Dateityp, leere oder beschädigte Datei) werden vor der fachlichen Verarbeitung abgefangen. Vorhersehbare Fehler werden als verständliche Meldung angezeigt statt als Python-Traceback.

---

## 10. Datenschutz und Betrieb

- Das Tool läuft vollständig lokal. Die hochgeladene Datei wird nur im Arbeitsspeicher verarbeitet und weder gespeichert noch an einen Dienst übertragen. Der Server ist nur über `localhost` erreichbar, und die Streamlit-Nutzungsstatistik ist abgeschaltet (`.streamlit/config.toml`).
- Ein echter Shopify-Export enthält häufig personenbezogene Daten (`Email`, `Billing Name`, `Shipping Address` usw.). Das Tool liest nur vier Spalten und ignoriert alle anderen. Weil nichts das Gerät verlässt, ist keine Vorbereitung der Datei nötig.
- Dateiinhalte werden nie in Logs oder Fehlermeldungen geschrieben.
- Echte Exporte gehören nicht ins Repository. `.gitignore` schließt `*.csv`, `*.xlsx` und ähnliche Dateien aus. Einzige Ausnahme ist die synthetische Demodatei `sample_data/demo_bestellungen.csv`. `.gitignore` wirkt nur für Dateien, die noch nie committet wurden: Eine einmal committete Datei bleibt in der Historie sichtbar.
- Sollte das Tool einmal gehostet werden, schaltet `LAGERANALYSE_DEMO=1` einen Hinweis ein, keine echten Daten hochzuladen.
- Alle Berechnungen erfolgen ohne Gewähr. Die Entscheidung, ob bestellt wird, bleibt beim Nutzer (Hinweis in der Fußzeile).
