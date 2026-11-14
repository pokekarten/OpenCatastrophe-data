<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# KNMI: Messhöhe, historische Korrekturen und Stationspositionen

Am 14. November 2026 wurde der Originalbericht **Potentiële wind update 2013
met nieuwe beschuttingsfactoren en metadata**, IR 2014-03, heruntergeladen
und mit `pdftotext -layout` lokal ausgewertet. Die
[Quittung](../../research/observations/knmi_wind_metadata_review.json) enthält
Original-URL, SHA256 und die Grenzen der Übertragbarkeit. PDF und extrahierter
Volltext bleiben außerhalb Git. Seitenangaben beziehen sich auf die gedruckten
Seitennummern, nicht den PDF-Viewer-Zähler.

## Fachlich relevante Ergebnisse

- Der Bericht definiert Umax als maximale **3-Sekunden-Mittelböe innerhalb
  einer Stunde** aus KIS (Methodenteil, gedruckte Seite 3). Das ist ein
  belastbarer Hinweis auf die historische Variable, aber noch kein Beleg,
  dass jede heutige FX-Archivversion dieselbe Verarbeitung verwendet.
- Anhang 6, Seite 64, beschreibt Höhenkorrekturen: Stunden-/10-Minuten-Mittel
  werden durch `fhfactor`, Böen durch `fxfactor` geteilt. Die Tabelle ist
  ausdrücklich ein KIS-Snapshot vom **5. August 2013**.
- Für De Bilt (260), Vlissingen (310) und Hoek van Holland (330) sind
  Korrekturperioden in den 1990ern bis 2011 dokumentiert. Ab Dezember 2007
  unterscheiden sich in dieser Tabelle Mittelwind- und Böenkorrektur.
- Anhang 8, Seite 66, beschreibt die Abschaffung der Korrektur im Mai 2011
  und rückwirkende Änderungen des Stundenmittels, die damals nicht gleichartig
  für FX erfolgt waren. Das beweist **keinen heute noch bestehenden Fehler**
  der geladenen Archive; es verhindert aber ihre pauschale Interpretation
  als rohe, einheitliche 10-Meter-Messungen.
- Anhang 2, Seiten 56–57, nennt für den **vorherigen Update-Stand** unter
  anderem 20 m für De Bilt, 27 m für Vlissingen und 15 m für Hoek van Holland.
  Diese Werte sind keine zeitlich gültige Höhenhistorie für alle Ereignisse
  und dürfen nicht unbesehen als heutige oder ereignisspezifische Höhe gelten.
- Anhang 7, Seite 65, vergleicht KIS- mit INFRA-Positionen (2011). Die
  Abweichungen betragen für 235: 495 m, 260: 217 m, 280: 82 m,
  310: 16 m, 330: 139 m. Für Schiphol nennt der Bericht 2.030 m und
  eine veraltete Stationsposition. Diese Positionsunterschiede sind nicht
  automatisch tatsächliche Stationsverlegungen.

## Konsequenz für den Modellvergleich

Vollständige 72-Stunden-Messfenster belegen nur Datenverfügbarkeit. Vor einer
Bias-Kalibrierung benötigen wir pro Ereignis die gültige Position,
Sensorhöhe und den Verarbeitungsstand der **heutigen Originaldatei**.
Weder aktuelle Stationskoordinaten noch der historische KIS-Snapshot ersetzen
diese Zuordnung. Eine automatische Rückkorrektur mit den Faktoren von 2013
könnte bereits korrigierte Daten ein zweites Mal verändern.

Die offizielle [KNMI-Erläuterung zur potentiellen Windgeschwindigkeit](https://www.knmi.nl/kennis-en-datacentrum/achtergrond/potentiele-wind)
beschreibt eine Normalisierung auf 10 m und Standardrauigkeit. Dieses
abgeleitete Produkt ist nicht einfach eine neue FX-Böenmessreihe; seine
Winddefinition und Korrekturen sind separat zu prüfen. Es wurde nicht als
Ersatz für FX in unser Modell eingesetzt.

**Entscheidung:** Noch keine numerische Windbias-Korrektur und keine
Behauptung einer abgeschlossenen unabhängigen Hazard-Validierung.
Die vorhandenen Fenster bleiben als Abdeckungsprüfung nutzbar. Der
Ereignis-Reader kennzeichnet die offene Stationsmetadatenprüfung nun
explizit maschinenlesbar, damit spätere Auswertungen Vollständigkeit
nicht mit Vergleichbarkeit verwechseln.

## Präzisierung aus Anhang 5, Seiten 60–61

Für Hoek van Holland entspricht die Stations-/Barometerposition ausdrücklich
nicht der Windmastposition. Der Bericht nennt für den Windmast vor Ende 2012
X=65492, Y=445057 und danach X=65292, Y=444475. Eine automatische
Umrechnung/Zuordnung wird hier nicht vorgenommen: Bezugskoordinatensystem
und genauer Übergangszeitpunkt müssen für den Ereignisvergleich bestätigt sein.

Der Bericht unterscheidet zudem physische Höhe und für die Homogenisierung
verwendete Rechenhöhe: Vlissingen 20 m über Land beziehungsweise 27 m über
Meer, Hoek van Holland vor 20121101 14,45 m über Land beziehungsweise
16,65 m über Meer. Für die damalige Aktualisierung wurden dennoch 27 m und
15 m beibehalten, um die vorhandenen Reihen nicht zusätzlich inhomogen zu
machen. Eine einzelne Zahl „Messhöhe“ beschreibt diese Verarbeitung daher
unzureichend. Die Werte aus Anhang 2 dürfen keine automatische Korrektur steuern.

## Zusätzliche technische Originalprüfung

Der Intake lehnt jetzt doppelte Spaltennamen und Archive mit Endpunkten
außerhalb der angeforderten Dekade ab. Alle zehn vorhandenen Originalarchive
wurden mit dieser Dekadenprüfung erneut gelesen. Zehn lokale Tests bestehen,
einschließlich falscher Dekade und doppelter FX-Spalte. Innere Datenlücken
werden weiterhin berichtet und nicht als vollständige Messungen ausgegeben.
