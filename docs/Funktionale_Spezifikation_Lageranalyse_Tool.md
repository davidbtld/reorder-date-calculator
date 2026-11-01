# Funktionale Spezifikation: Lager- und Trendanalyse-Tool für Shopify-Bestellexporte

**Zielgruppe:** Kleine Online-Shops auf Shopify — das Tool ist dank des Shopify-Standardexportformats für jeden Shopify-Shop nutzbar (siehe Schritt 2)
**Analyseprodukt:** Vom Nutzer nach dem Datei-Upload frei auswählbar (keine feste Produktbindung im Code) — Referenzbeispiel in diesem Dokument: "Produkt A" mit seinen Varianten ("Produkt A | Variante 1", "Produkt A | Variante 2" usw.)

---

## 1. Zielsetzung des Tools

Das Tool ermittelt auf Basis vergangener Shopify-Bestelldaten und eines manuell erfassten Ist-Lagerbestands, **wann die nächste Nachbestellung eines vom Nutzer ausgewählten Produkts (Referenzbeispiel: "Produkt A") ausgelöst werden muss**, damit das Unternehmen zu keinem Zeitpunkt in einen Fehlbestand (Out-of-Stock) gerät.

Das Tool ist bewusst als **zustandsloses Einzelanalyse-Tool** konzipiert: Jeder Durchlauf ist eine unabhängige Momentaufnahme. Es findet keine Speicherung zwischen Sitzungen statt (siehe Abschnitt 9, Scope-Grenzen).

---

## 2. Datengrundlage & Eingaben

### 2.1 Datei-Upload (Pflichteingabe)

- **Format:** CSV oder Excel (.xlsx), Export aus Shopify (Admin → Bestellungen → Exportieren)
- **Pflichtspalten:** `Name`, `Paid at`, `Lineitem quantity`, `Lineitem name`
- **Empfohlener Exportzeitraum:** mind. 90 Tage rückwirkend ab dem heutigen Datum
- **Herkunft der Daten:** manueller Export durch den User, keine Live-API-Anbindung (siehe Abschnitt 9)
- Die Datei kann zusätzlich beliebig viele weitere, für die Analyse irrelevante Spalten enthalten (z. B. `Email`, `Billing Address`, `Taxes`, `Financial Status`). Deren Vorhandensein, Reihenfolge oder Befüllungsgrad hat **keinen Einfluss** auf die Verarbeitung und darf nie zu einem Fehler führen.

### 2.2 Manuelle Eingabefelder

| Feld | Typ | Pflicht | Beschreibung |
|---|---|---|---|
| Aktueller Lagerbestand | Ganzzahl ≥ 0 | Ja | Physischer Ist-Bestand des Produkts zum Zeitpunkt der Tool-Nutzung ("heute") |
| Lieferzeit | Ganzzahl ≥ 0 (Tage) | Ja | Zeitspanne zwischen Bestellauslösung beim Lieferanten und Wareneingang |

**Hinweis:** Ein Pufferbestand ist in dieser Version explizit **nicht** Teil des Tools (siehe Abschnitt 9, Scope-Grenzen).

---

## 3. Datenverarbeitung

Die Verarbeitung erfolgt **immer** in exakt dieser Reihenfolge. Kein Schritt darf übersprungen oder vorgezogen werden, da spätere Schritte auf den Ergebnissen der vorherigen aufbauen.

### Schritt 1 — Einlesen der Datei

Die hochgeladene Datei wird eingelesen und auf Vorhandensein der vier Pflichtspalten (`Name`, `Paid at`, `Lineitem quantity`, `Lineitem name`) geprüft. Fehlt eine dieser Spalten, bricht die Verarbeitung mit einer konkreten Fehlermeldung ab (siehe Abschnitt 7). Alle anderen Spalten werden ignoriert.

### Schritt 2 — Produktauswahl und Produktfilter

**Grundidee:** Die Spaltenstruktur eines Shopify-Exports (`Name`, `Paid at`, `Lineitem quantity`, `Lineitem name`) ist über alle Shopify-Shops hinweg identisch, nur die *Werte* (Produktnamen) unterscheiden sich. Der Produktname wird deshalb zur Laufzeit vom Nutzer ausgewählt und nicht im Code festgelegt.

**Ablauf:**

1. Nach dem erfolgreichen Einlesen der Datei (Schritt 1) ermittelt das Tool die Liste aller **eindeutigen, tatsächlich in der Datei vorkommenden Werte** der Spalte `Lineitem name`.
2. Diese Liste wird dem Nutzer als **Mehrfachauswahl** angezeigt (z. B. alle Varianten eines Produkts: "Produkt A | Variante 1", "Produkt A | Variante 2" usw.).
3. Der Nutzer wählt eine oder mehrere dieser Werte aus, die zusammen "das" zu analysierende Produkt ergeben.
4. Es werden **ausschließlich** Zeilen weiterverarbeitet, deren `Lineitem name` **exakt** einem der ausgewählten Werte entspricht (Gleichheitsvergleich, kein Präfix- oder Teilstring-Match mehr nötig, da die Auswahl bereits aus den real vorhandenen Werten erfolgt).
5. **Verbindliche Reihenfolge:** Dieser Zeilenfilter wird erst **nach** dem Forward-Fill von `Paid at` (Schritt 3) auf die Zeilen angewendet. Grund: `Paid at` steht nur in der ersten Zeile einer Bestellung, und diese Zeile kann zu einem anderen Produkt gehören als die ausgewählte Zeile. Würde zuerst gefiltert, ginge das Datum verloren und gültige Verkäufe würden fälschlich ausgeschlossen. Die Liste der Auswahlwerte (Punkte 1–3) wird aus allen Zeilen der Datei gebildet.

**Warum das robuster ist als ein Textfilter (Präfix- oder Freitext-Suche):**
- Es gibt keine Tippfehler, keine Groß-/Kleinschreibungsprobleme und kein Rate-Verhalten (Fuzzy-Matching) mehr, da nicht getippt, sondern aus echten, vorhandenen Werten ausgewählt wird.
- Das Tool funktioniert dadurch unverändert für jedes beliebige Shopify-Unternehmen und jeden beliebigen Produktnamen, ohne Codeänderung.
- Führende/nachfolgende Leerzeichen werden beim Aufbau der Auswahlliste getrimmt, damit nicht zwei optisch identische Werte fälschlich als unterschiedliche Einträge auftauchen.

**Validierung:** Trifft der Nutzer keine Auswahl, wird die Berechnung nicht gestartet (siehe Abschnitt 7, Fehlerbehandlung). Alle Zeilen, deren `Lineitem name` zu keinem ausgewählten Wert passt, werden endgültig verworfen und fließen in keinen der folgenden Schritte ein.

### Schritt 3 — Gruppierung nach Bestellnummer und Forward-Fill von `Paid at`

Ein Shopify-Bestellexport ist **zeilenbasiert pro Position (Lineitem)**, nicht pro Bestellung. Die Spalte `Name` enthält die Bestellnummer. Kauft eine Person in einem Bestellvorgang mehrere Positionen (z. B. mehrere Einheiten desselben Produkts über getrennte Zeilen), erscheint dieselbe Bestellnummer mehrfach hintereinander.

**Wichtige Eigenheit realer Shopify-Exporte:** Bestellbezogene Felder wie `Paid at` werden nur in der **ersten Zeile** einer mehrzeiligen Bestellung befüllt; alle weiteren Positionszeilen derselben Bestellung lassen dieses Feld leer, obwohl sie zur selben, bezahlten Bestellung gehören.

Daraus ergibt sich folgende verbindliche Regel:

1. **Alle** Zeilen der Datei (noch **nicht** nach Produkt gefiltert, siehe Schritt 2, Punkt 5) werden nach `Name` gruppiert.
2. Innerhalb jeder Gruppe wird der **erste vorhandene, gültig parsebare** `Paid at`-Wert ermittelt und auf **alle** Zeilen dieser Gruppe übertragen (Forward-Fill).
3. Danach wird der Produktfilter aus Schritt 2 angewendet: Es bleiben nur Zeilen, deren `Lineitem name` exakt einem ausgewählten Wert entspricht.
4. Enthält eine Bestellgruppe **keinen einzigen** gültig parsebaren `Paid at`-Wert (Wert leer oder nicht lesbar), gilt die **gesamte Bestellung** als ungültig: Alle ihre Zeilen werden verworfen und als **eine** Einheit (nicht einzeln pro Zeile) in der Fehlerstatistik gezählt. Gezählt werden nur Bestellungen, die mindestens eine Zeile eines **ausgewählten** Produkts enthalten, damit Bestellungen mit fremden Produkten die Meldung nicht verfälschen.
5. **Es findet keine Deduplizierung oder Zusammenfassung nach `Name` statt.** Jede Zeile bleibt nach dem Forward-Fill weiterhin einzeln bestehen und wird einzeln in die spätere Summenbildung (Schritt 6) einbezogen. Eine wiederkehrende Bestellnummer ist niemals ein Hinweis auf einen Duplikat-Datensatz. Kauft eine Person 20 Stück in einem Bestellvorgang — sei es als eine Zeile mit `Lineitem quantity = 20` oder verteilt auf mehrere Zeilen mit derselben Bestellnummer — werden in beiden Fällen alle 20 Einheiten vollständig gezählt.

Die Bestellnummer selbst geht in keine Berechnung ein; sie dient ausschließlich der korrekten Gruppierung in diesem Schritt.

### Schritt 4 — Zeilenbereinigung

Nach dem Forward-Fill (Schritt 3) werden die verbleibenden Zeilen wie folgt geprüft:

- Zeilen, deren `Paid at` (nach Forward-Fill) weiterhin leer oder **nicht als gültiges Datum parsebar** ist, werden verworfen. Ein nicht parsebarer Wert (z. B. `17:18.21` statt `17:18:21` — ein in der Praxis vorkommender manueller Tippfehler) zählt dabei ausdrücklich als **ungültig**, nicht als Platzhalter oder Näherung. Solche Fälle werden dem User separat gemeldet: "X Bestellung(en) ohne gültiges Zahlungsdatum (Paid at leer oder nicht lesbar) aus der Analyse ausgeschlossen."
- Zeilen mit **negativer `Lineitem quantity`** (Retoure/Storno) werden **nicht** in die Verkaufssumme eingerechnet, sondern separat gezählt und informativ ausgewiesen ("X Retouren im Datenzeitraum erkannt, nicht in Trend eingerechnet."). Diese Vereinfachung ist eine bewusste Scope-Entscheidung (siehe Abschnitt 9).
- Zeilen mit `Lineitem quantity` = 0 oder einem nicht-numerischen Wert werden verworfen und gezählt; Meldung: „X Zeile(n) mit ungültiger Menge verworfen.“

**Begründung "Paid at" als Referenzdatum:** Das Tool verwendet das Zahlungsdatum als den Zeitpunkt, an dem der Artikel als verkauft gilt. Eine mögliche zeitliche Differenz zwischen Zahlung und tatsächlichem Warenausgang (z. B. bei Backorder) wird bewusst nicht abgebildet — eine dokumentierte Vereinfachung, keine Fehlfunktion.

### Schritt 5 — Abdeckungsprüfung des Datenzeitraums

Das Trendfenster **endet immer am heutigen Systemdatum** (inklusive heute) und umfasst höchstens 90 Kalendertage: Fenster-Beginn = heute − 89 Tage. Zeilen außerhalb des Fensters (älter als der Fenster-Beginn oder mit Datum nach heute) werden für den Trend ignoriert.

Die **Anzahl abgedeckter Tage** wird **inklusive** beider Randtage berechnet:

```
effektiver Beginn   = späteres von (Fenster-Beginn, ältestes gültiges Paid-at-Datum der verbliebenen Zeilen)
Anzahl abgedeckter Tage = (heute − effektiver Beginn) in Tagen + 1
```

Dadurch ist die Anzahl abgedeckter Tage stets ≥ 1; eine Division durch null ist ausgeschlossen (auch wenn alle Verkäufe am selben Tag liegen). Liegt das neueste Datum in der Datei weit vor heute, sinkt der Trend entsprechend, weil die Tage ohne Verkäufe bis heute mitzählen. Das ist gewollt.

- Ist die Anzahl abgedeckter Tage **= 90**: Die Trendberechnung erfolgt auf Basis der letzten 90 Tage.
- Ist die Anzahl abgedeckter Tage **< 90**: Die Trendberechnung erfolgt auf Basis des tatsächlich vorhandenen Zeitraums, und das Tool zeigt folgenden Warnhinweis:
 > "Die hochgeladene Datei deckt nur {X} Tage ab. Der berechnete Trend basiert auf einem verkürzten Zeitraum und kann weniger belastbar sein."

### Schritt 6 — Trendberechnung

```
Trend (Stück/Tag) = Summe aller gültigen "Lineitem quantity"-Werte
                     ÷ Anzahl abgedeckter Tage (aus Schritt 5)
```

**Sonderfall Trend = 0** (keine gültigen Verkäufe im Zeitraum): Das Tool berechnet **keinen** Reorder Point und **keine** Tage-bis-Bestellung, sondern zeigt stattdessen:
> "Im gewählten Zeitraum wurden keine Verkäufe des Produkts erfasst. Eine Trendberechnung ist nicht möglich."

### Schritt 7 — Referenzzeitpunkt "heute" und Lagerbestandslogik

"Heute" ist ausnahmslos das **tatsächliche Systemdatum** zum Zeitpunkt der Tool-Nutzung — nicht das jüngste Datum in der hochgeladenen Datei. Es ist zugleich das Ende des Trendfensters (Schritt 5).

**Verbindliche Festlegung (verhindert Doppelabbuchung):** Der in Abschnitt 2.2 manuell eingegebene Lagerbestand ist der physische Ist-Bestand **zum heutigen Zeitpunkt**, also bereits nach Abzug aller bisherigen, auch der in der Datei enthaltenen, Verkäufe. Die Datei-Verkäufe werden **ausschließlich zur Trendberechnung (Schritt 6)** verwendet und **niemals zusätzlich** vom eingegebenen Lagerbestand abgezogen.

---

## 4. Berechnungslogik (Kernformeln)

```
Reorder Point (Stück) = Trend (Stück/Tag) × Lieferzeit (Tage)
```

**Bedeutung:** Der Reorder Point (deutsch: **Meldebestand**) ist ein **Lagerbestand**, kein Bestellvolumen. Er gibt an, bei welchem Lagerbestand die Bestellung spätestens ausgelöst werden muss, damit der Bestand bis zum Wareneingang reicht. Wie viel bestellt wird (Bestellmenge), berechnet das Tool nicht (siehe Abschnitt 9). In der Oberfläche heißt die Kennzahl „Meldebestand" mit der Erläuterung „Stück · Bei diesem Bestand bestellen" (gemeint: Die Bestellung ist auszulösen, sobald der Lagerbestand diesen Wert erreicht oder unterschreitet); im Code und in diesem Dokument bleibt der Fachbegriff „Reorder Point" erhalten.

```
WENN aktueller Lagerbestand ≤ Reorder Point:
    → Ausgabe: "Bestellung muss SOFORT ausgelöst werden." (Dringlichkeit: kritisch)

SONST:
    Tage bis Bestellpflicht = (aktueller Lagerbestand − Reorder Point) ÷ Trend
    Bestelldatum = heutiges Datum + Tage bis Bestellpflicht (abgerundet auf ganze Tage)
    → Ausgabe: Hauptkachel „Spätestens bestellen am“ mit dem Bestelldatum (Details in Abschnitt 5.1)
    → Dringlichkeit nach Tagen bis Bestellpflicht: ≥ 8 = ok (grün), 3–7 = Warnung (orange), 0–2 = kritisch (rot)
```

**Rundungsregel:** "Tage bis Bestellpflicht" wird stets **abgerundet** (nicht kaufmännisch gerundet), um im Zweifel eher zu früh als zu spät auf eine Bestellung hinzuweisen.

---

## 5. Ausgabe des Tools

Nach erfolgreicher Berechnung zeigt das Tool folgende Werte an:

1. Anzahl der für die Analyse berücksichtigten Zeilen (nach Filter und Bereinigung) sowie Anzahl der zugrundeliegenden Bestellungen
2. Abgedeckter Datenzeitraum in Tagen (inkl. Warnhinweis bei < 90 Tagen)
3. Berechneter Trend in Stück/Tag
4. Berechneter Reorder Point in Stück
5. Klarer Handlungshinweis: entweder „Jetzt bestellen“ (Kennzeichen „Sofort“) oder das konkrete späteste Bestelldatum
6. Informative Hinweise zu ausgeschlossenen Daten: Anzahl Bestellungen ohne gültiges Zahlungsdatum, Anzahl erkannter Retouren, Anzahl Zeilen mit ungültiger Menge
7. Diagramm des Absatzverlaufs (siehe 5.1)

### 5.1 Diagramm und Formate

- **Inhalt:** Liniendiagramm der verkauften Stückzahl des ausgewählten Produkts, aggregiert pro Kalenderwoche (Montag bis Sonntag, beschriftet als „KW 18“).
- **Zeitraum:** die letzten 6 Monate bis heute, unabhängig vom 90-Tage-Trendfenster. Die erste Woche ist die Kalenderwoche, in die das Datum „heute − 6 Monate“ fällt; die letzte ist die laufende Woche, die nur Verkäufe bis heute enthält (der letzte Punkt liegt daher meist niedriger; die Diagramm-Unterzeile weist darauf hin: „laufende Woche bis heute“). Reicht die Datei nicht so weit zurück, wird nur der vorhandene Zeitraum gezeigt. Wochen ohne Verkäufe erscheinen mit dem Wert 0.
- **Achsen:** x = Kalenderwoche, y = Stück pro Woche, y-Achse beginnt bei 0.
- **Darstellung:** eine einzelne blaue Linie mit kleinen Datenpunkten auf hellem Diagrammhintergrund; das 90-Tage-Trendfenster ist im Diagramm hellblau hinterlegt und beschriftet („Trendfenster (90 Tage)"). Die x-Achse beschriftet mindestens die erste und die letzte Kalenderwoche, die y-Achse zeigt nur ganze Zahlen, beginnend bei 0.
- **Gestaltung der Oberfläche (Business-Stil):** Sachlicher Stil, wie bei Unternehmenssoftware üblich. Dunkle Kopfleiste in Blaugrau mit Logo-Platzhalter und Titel „Lageranalyse"; darunter Seitentitel mit einer erklärenden Zeile; eine Filterleiste, die Upload, Produktauswahl, „Aktueller Lagerbestand (Stk)“ und „Lieferzeit (Tage)“ in einer Reihe enthält (Beschriftung über jedem Feld; bei Upload und Produktauswahl erklärt ein Hilfesymbol „?“ das Feld); Kennzahlen als Kacheln (fünf Kacheln in einer Reihe); Diagramm in einer weißen Karte; Fußzeile mit dem Haftungs- und Datenschutzhinweis. Heller grauer Hintergrund, weiße Karten mit dünner Umrandung und leichtem Schatten, Akzentfarbe Blau, serifenlose System-Schrift. Rein dekorative Elemente ohne Funktion (Benutzer-Avatar, Navigationspfad) werden nicht umgesetzt. Farben und Schrift sind in einer zentralen Theme-Einstellung änderbar.
- **Semantische Farben:** Grün = unkritisch (Hauptkachel mit ausreichend Vorlauf), Orange = Hinweis/Warnung (Ausschlüsse, verkürzter Zeitraum, Hauptkachel mit knappem Vorlauf), Rot = dringend oder Fehler (Hauptkachel mit sehr knappem Vorlauf, „Jetzt bestellen", Fehlermeldungen), Blau = Information (z. B. Trend = 0). Alle Hinweise, Warnungen und Fehlermeldungen erscheinen als farbige Meldungsleiste unterhalb der Filterleiste; die orange Leiste erscheint nur, wenn mindestens ein Hinweis vorliegt (jede Zeile nur, wenn ihre Zahl größer als 0 ist; bei einer sauberen Datei fehlt die Leiste ganz); mehrere Ausschluss-Hinweise stehen untereinander in einer orangen Leiste, jeweils mit dem Wortlaut aus Schritt 4 („X Bestellung(en) ohne gültiges Zahlungsdatum (Paid at leer oder nicht lesbar) aus der Analyse ausgeschlossen.“, „X Retouren im Datenzeitraum erkannt, nicht in Trend eingerechnet.“, „X Zeile(n) mit ungültiger Menge verworfen.“).
- **Hauptkachel:** Zeigt „Spätestens bestellen am" mit dem Datum im Format TT.MM.JJJJ und einem Statuskennzeichen mit den verbleibenden Tagen („In 16 Tagen"; bei 0 Tagen: „Heute"). Im Fall „sofort bestellen" zeigt sie stattdessen „Handlungsbedarf" mit dem Text „Jetzt bestellen" in Rot und dem Kennzeichen „Sofort"; zusätzlich erscheint eine rote Meldungsleiste „Bestellung muss SOFORT ausgelöst werden." mit dem Vergleich „Aktueller Lagerbestand X ≤ Meldebestand Y".
- **Farbe der Hauptkachel (Dringlichkeit):** Die Farbe richtet sich nach den Tagen bis zum spätesten Bestelldatum: **8 oder mehr Tage = grün**, **3 bis 7 Tage = orange**, **0 bis 2 Tage = rot** (0 Tage = „Heute"). Ist der aktuelle Lagerbestand ≤ Meldebestand, ist die Kachel rot mit „Jetzt bestellen". Die Schwellen (7 und 2 Tage) stehen in `config.py`. Das Statuskennzeichen nennt immer auch den Text („In 5 Tagen"), die Farbe ist nie der einzige Hinweisgeber. Es gibt kein Blinken. Die Hauptkachel ist eine reine Anzeige, keine Schaltfläche.
- **Weitere Kacheln:** Trend (Stück pro Tag, drei Nachkommastellen, deutsches Dezimalkomma), Meldebestand (Reorder Point; Stück, eine Nachkommastelle, mit der Erläuterung „Stück · Bei diesem Bestand bestellen"), Datenzeitraum (Tage und Datumsspanne, z. B. „90 Tage“ und „31.07. – 28.10.2026“) und Berücksichtigt (Zeilen und Bestellungen).
- **Datumsformat in der Ausgabe:** TT.MM.JJJJ (z. B. 24.06.2026). Das späteste Bestelldatum wird in diesem Format angezeigt.
- **Oberflächenskizze:** siehe `docs/skizze_oberflaeche.png` (Anordnung der Elemente, nicht pixelgenau verbindlich). Die Skizze zeigt oben die Seite im Normalfall (aktueller Lagerbestand 120, Stichtag 28.10.2026: spätestens bestellen am 13.11.2026). Der Bereich darunter („Legende") ist nur ein Hilfsmittel der Skizze: Er zeigt die vier möglichen Zustände der Hauptkachel nebeneinander. Im Tool erscheint immer genau **eine** Hauptkachel (oben links in der Kachelreihe), und es gibt keine Legende. Die rote Meldungsleiste erscheint nur im Zustand „Jetzt bestellen", unterhalb der Filterleiste.

---

## 6. Datenmodell im Überblick

| Spalte | Verwendung im Tool |
|---|---|
| `Name` | Nur zur Gruppierung (Schritt 3), fließt in keine Berechnung ein |
| `Paid at` | Referenzdatum für Trend- und Zeitraumberechnung (nach Forward-Fill) |
| `Lineitem quantity` | Menge je Zeile, Grundlage der Trendsumme |
| `Lineitem name` | Grundlage der Produktauswahl und des Produktfilters (Schritt 2) |
| alle übrigen Spalten | werden vollständig ignoriert |

---

## 7. Fehlerbehandlung (Edge Cases)

| Fall | Verhalten des Tools |
|---|---|
| Datei enthält nicht alle Pflichtspalten (`Name`, `Paid at`, `Lineitem quantity`, `Lineitem name`) | Abbruch mit konkreter Fehlermeldung, welche Spalte(n) fehlen |
| Nutzer trifft keine Produktauswahl (Schritt 2) | Validierungsfehler, Berechnung wird nicht gestartet: "Bitte mindestens einen Produktnamen auswählen." |
| Datei enthält keine Zeile, die zu einem ausgewählten Produktnamen passt (sollte durch Schritt 2 praktisch ausgeschlossen sein, da nur real vorkommende Werte zur Auswahl stehen) | Abbruch mit Hinweis: "Keine Datensätze für die ausgewählten Produkte gefunden." |
| Eine Bestellgruppe hat keinen gültig parsebaren `Paid at`-Wert | Gesamte Bestellung wird ausgeschlossen und als eine Einheit gezählt (siehe Schritt 3) |
| Einzelne Zeile hat ein nicht parsebares Datum, andere Zeilen derselben Bestellung sind gültig | Nach Forward-Fill unerheblich, da der gültige Wert aus der Gruppe übernommen wird |
| Trend = 0 | Keine Reorder-Berechnung, siehe Schritt 6 |
| Lagerbestand oder Lieferzeit nicht eingegeben oder negativ | Die Eingabefelder starten **leer** (keine Vorbelegung). Ohne Eingabe wird der davon abhängige Teil nicht berechnet: Trend, Datenzeitraum, Berücksichtigt und Diagramm erscheinen, sobald Datei und Produkt gewählt sind. Der Meldebestand erscheint, sobald die Lieferzeit eingegeben ist. Die Hauptkachel erscheint erst, wenn beide Felder ausgefüllt sind; bis dahin zeigt eine blaue Hinweisleiste „Bitte aktuellen Lagerbestand und Lieferzeit eingeben.“ Negative Werte sind ein Validierungsfehler. Der Wert 0 ist eine gültige Eingabe. |
| Lagerbestand = 0 | Gültiger Fall; führt automatisch zu "Bestellung muss sofort ausgelöst werden", sofern Trend > 0 |

---

## 8. Nicht-funktionale Anforderungen

- Upload-Verarbeitung soll für Dateien bis zu einigen zehntausend Zeilen performant bleiben (kein zeilenweises Neu-Einlesen bei jeder Eingabefeld-Änderung).
- Änderungen an den manuellen Eingabefeldern (Lagerbestand, Lieferzeit) sollen die Ausgabe **ohne erneuten Upload** neu berechnen, da Trend und abgedeckter Zeitraum nach Schritt 6 im Anwendungszustand zwischengespeichert vorliegen.

---

## 9. Bewusste Scope-Grenzen & Annahmen (explizit dokumentiert)

Diese Punkte sind **keine offenen Fragen**, sondern bewusst getroffene Entscheidungen für den aktuellen Projektumfang:

1. **Ein-Produkt-Tool pro Durchlauf:** Pro Analyse wird genau eine vom Nutzer ausgewählte Produktgruppe betrachtet (siehe Schritt 2) — keine gleichzeitige Mehrprodukt-Übersicht/Dashboard in einem Durchlauf. Da die Auswahl zur Laufzeit aus den tatsächlich vorhandenen Werten erfolgt, ist das Tool damit nicht auf "Produkt A" oder ein bestimmtes Unternehmen festgelegt, sondern mit jedem Shopify-Export nutzbar.
2. **Kein persistenter Speicher:** Lagerbestand und Lieferzeit werden bei jeder Nutzung neu eingegeben; keine Datenbank, keine sitzungsübergreifende Fortschreibung.
3. **Kein Live-API-Zugriff auf Shopify:** Datengrundlage ist ein manueller CSV/Excel-Export.
4. **Kein Pufferbestand:** Ein Sicherheitsbestand ist in dieser Version nicht implementiert.
   **Keine Bestellmenge:** Das Tool nennt, *wann* bestellt werden muss (Meldebestand und spätestes Bestelldatum), aber nicht, *wie viel*. Die Bestellmenge hängt von Faktoren ab, die das Tool nicht kennt (Mindestabnahme, Budget, Lagerplatz, gewünschte Reichweite); sie ist eine mögliche spätere Erweiterung.
5. **Retouren/Stornos** werden nicht in den Trend eingerechnet, aber auch nicht vom Lagerbestand zurückgebucht — nur informativ ausgewiesen.
6. **`Paid at` statt `Fulfilled at`** als Verkaufszeitpunkt (siehe Begründung in Schritt 4).
7. **`Financial Status` wird nicht ausgewertet.** Die Gültigkeit einer Bestellung hängt ausschließlich am (forward-gefüllten) `Paid at`-Wert. Nachträgliche Stornierungen oder Erstattungen, die sich nur über `Financial Status` (z. B. "refunded") zeigen, werden im aktuellen Scope nicht erkannt.
8. **Keine aktive Prüfung auf personenbezogene Daten in der Datei.** Das Tool liest und verarbeitet ausschließlich die vier Pflichtspalten; es prüft aber nicht aktiv, ob die hochgeladene Datei zusätzlich personenbezogene Kundendaten (z. B. `Email`, `Billing Name`, `Shipping Address`) enthält, und entfernt diese auch nicht automatisch. Der vollständige Shopify-Export kann unverändert verwendet werden; alle übrigen Spalten werden ignoriert. Da die Anwendung lokal läuft und keine Daten überträgt, ist keine Vorbereitung der Datei nötig (siehe Architektur- und Code-Richtlinien, Abschnitt „Datenschutz“, für den Hintergrund).

---

## 10. Mögliche spätere Erweiterungen (außerhalb des aktuellen Scopes)

- Wiedereinführung eines konfigurierbaren Pufferbestands in der Reorder-Formel
- Unterstützung mehrerer Produkte mit individuellen Reorder-Parametern
- Persistente Speicherung des Lagerbestands (Datenbank) zur automatischen Fortschreibung zwischen Sitzungen
- Live-Anbindung an die Shopify Admin API zur automatisierten Datenaktualisierung
- Gewichtete Trendberechnung (z. B. exponentielle Glättung) statt einfachem Durchschnitt
- Klappbereich „Wie wurde das berechnet?“, der die Berechnungsschritte (Filter, Gruppierung, Trend, Meldebestand) für den Nutzer nachvollziehbar macht
- Auswertung von `Financial Status` (z. B. Ausschluss von "refunded"/"voided") als zusätzliches, von `Paid at` unabhängiges Gültigkeitskriterium
