<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Mehrsturmfenster aus originalen KNMI-Stundenarchiven

Der lokale Originaldatenlauf über die Stationen 235, 260, 280, 310 und 330
ergab jeweils 29 vollständige 72-Stunden-Fenster aus den 50 ERA5-CLIMK-Labels.
Alle fünf Stationen decken dieselben 29 Ereignisse ab: insgesamt 145
vollständige Stations-Ereignis-Fenster. Die Daten reichen 2001–2020, während
CLIMK bereits 1995 beginnt; fehlende frühere Ereignisse werden nicht ergänzt.

Der [Runner](../../research_runners/knmi_climk_complete_event_windows.py)
verwendet `--archive-dir EXTERN --hazard ORIGINAL.nc --output EXTERN.json`.
Er erhält die Original-Sturmindizes und Datumslabels, erfasst Eingabehashes,
prüft doppelte Stundenlabels und berechnet Spitzen nur aus 72 vorhandenen
Werten. KNMI-Stunden 1–24 werden auf UTC-Stundenendpunkte abgebildet. Je
CLIMK-Datum werden die 72 Endpunkte vom Vortag 01:00 bis Folgetag 24:00
gewählt. Diese explizite Hypothese ersetzt keine Prüfung der ursprünglichen
CLIMK-Aggregationsgrenzen. Fehlende Werte bleiben unbekannt.

Vollständig verfügbare CLIMK-Namen im tatsächlichen Originaldatenlauf:

KYRILL, ANDREA, JEANETT, EMMA, FRANZ, DIRK, KIRSTEN, MIKE-NIKLAS, ILONA, LOTTE, ERWIN-DIMITRI, GUNTER, FRIDTJOF, ANNA, CHRISTIAN_STJUDE, JENNIFER, XAVER, NINA-ORALIE, JOACHIM, CARMEN, TINI-ULLA, NILS, JETTE, FRIEDHELM, BECKY, XYNTHIA, ULRIKE, ULF, CALVANN.

Die Fenster sind ein Beobachtungsdatensatz für ausgewählte Ereignisse,
kein vollständiger Jahreskatalog. Messhöhe, Instrumentengeschichte,
Böenmittelung, Qualitätskennzeichen und Rechte sind vor Kalibrierung weiter
zu prüfen. Die fünf Messreihen desselben Sturms ergeben keine fünf unabhängigen
Ereignisse. Dieser Schritt bildet noch keine Stationswerte auf CLIMK-Zellen
ab und passt keine Korrekturfunktion an.

Quelle und Attribution: Royal Netherlands Meteorological Institute (KNMI);
CLIMK-WINDS v2 ERA5, Flynn et al. (2025).
