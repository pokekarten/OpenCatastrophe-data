<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windstorm Europe: Umsetzung und Datenbeschaffung

Stand 2026-11-14. Arbeitsannahme: europäische außertropische Stürme,
Gebäudeschäden und explizite Versicherungsbedingungen. „Winston York“ wird
im Gesprächskontext als Windstorm Europe verstanden; kein New-York-Modell.
Ein perfektes Modell lässt sich nicht zusichern. Ziel sind nachvollziehbare
Ereignisse, belegte Eingaben, unabhängige Validierung und quantifizierte Unsicherheit.

## Architektur und prüfbare Liefergegenstände

1. **Originalarchiv:** externe unveränderte Dateien, SHA256, Quelle, Abruf,
   Rechte, Version und Parser. Repo enthält Code und Belege, keine automatisch
   weiterveröffentlichten Originaldaten. Dauerhafter Speicher bleibt erforderlich.
2. **Ereignisebene:** physische Ereignis-ID getrennt von Quell-ID,
   Tracker, Ensemble, Kalibrierungsvariante und Versicherungs-Stundenklausel.
   Historisches Jahresinventar zuerst; vollständige Zeitabdeckung und Nulljahre.
3. **Gefährdung:** Winddefinition, Zeitfenster, Raster, Einheiten, Masken,
   Qualitätskennzeichen. Lokale Korrekturen nur mit überprüfter Referenz;
   keine doppelte Geländekorrektur. Fehlende Gefährdung bleibt fehlend.
4. **Exposition:** stabile Gebäude-ID, Geometrie, Nutzung, Alter, Höhe,
   Dach, Bezugsfläche, Wiederherstellungswert und Preisjahr. Bestandsdaten
   und tatsächlich versicherte Risiken strikt unterscheiden.
5. **Vulnerabilität:** benannte Gebäudeklassen, Kurvenherkunft,
   Wahrscheinlichkeit eines Schadens und bedingte Schadenhöhe. Klassenmischung,
   Streuung und Ereignisabhängigkeit explizit; Sensitivität statt stiller Ersatzwerte.
6. **Verlustrechnung:** physischer Schaden → Police → Rückversicherung;
   unabhängige Rechenorakel, Summenerhaltung und Oasis-Abgleich.
7. **Jahresrisiko:** erst bei überprüften Häufigkeiten/Ensemblezeiten
   AAL/OEP/AEP berechnen; Sturmserien und grenzübergreifende Korrelation erhalten.
8. **Validierung:** Kalibrierung und Ereignis-/Länder-Holdouts trennen;
   Wind, Gebäude, Werte, Schäden und Finanzrechnung separat beurteilen.

## Beschaffungsfolge

| Priorität | Daten | Aktion und tatsächliche Grenze |
|---|---|---|
| 1 | C3S EWS Tracks + Footprints, ein Tracker | Vollständiges Pilotjahr, danach historischer Zeitraum. Hier fehlen CDS-Konfiguration und API-Schlüssel; keine erfolgreichen Originaldownloads behauptet. Produktbedingungen und Benutzerzugang erforderlich. |
| 1 | DWD/KNMI/Météo-France Messungen | Vorhandene Daten nutzen, KNMI um 1981–2000 erweitern. Stationshistorie, Böendauer, Höhe und Zeitfenster vor wissenschaftlicher Freigabe prüfen. |
| 1 | Schadenbeobachtungen mit Exposition | EIOPA/GDV/nationale Quellen auf Windanteil, Bezugsbestand, Preisjahr und Deckung prüfen. C3S Tier-3-Modellverluste sind kein unabhängiger Beobachtungsersatz. |
| 2 | Nationale Gebäude und harmonisierte Ergänzungen | DE/NL/FR/UK als Pilotfolge; Register vor globaler Dublettenanreicherung. Regionen vollständig prüfen, dann erweitern. |
| 2 | Absolute Baukosten und Indizes | Quellen nach Land/Klasse und Bezugsfläche; Eurostat-Index allein liefert keine EUR/m². |
| 2 | WISC Inventar und synthetische Felder | Ensemble und Kalibrierungsvarianten erhalten. Bereits vorhandener WISC-Preflight nennt simulierte Zeitlücken; fehlende Monate sind keine Nullereignismonate. |
| 3 | DEM, Landbedeckung, Rauigkeit | Gezielte Ausschnitte für validierte lokale Windkorrekturen; keine unkontrollierte Sammlung ganzer Kontinentraster. |

## Ausgeführter Schritt: historische KNMI-Originale

Der neue [Download-Reader](../../research_runners/knmi_historical_wind_acquisition.py)
beschafft die Jahrzehnte 1981–1990 und 1991–2000 für Stationen
235, 260, 280, 310 und 330 vom öffentlichen KNMI-CDN. Das ergänzt die
bereits bearbeiteten Jahrzehnte 2001–2020 und erlaubt zusätzliche historische
Sturmvergleiche, ohne historische Schaden- oder Windvalidierung vorzutäuschen.

Originalformat: unkommentierter Metadatenvorspann vor `# STN,`.
Der erste Lauf erkannte diesen Vorspann fälschlich als Datenzeile und lehnte
alle Antworten ab. Der Reader beginnt nun erst nach dem exakten Tabellenheader;
fehlerhafte Datenzeilen werden weiterhin abgelehnt. Der Regressionstest enthält
diesen Vorspann. Geprüft werden ZIP-Größe, Stationsidentität, Stunden 1–24,
Dubletten, negative Böen sowie fehlende Werte und Stunden. HH=24 wird korrekt
auf 00 Uhr des Folgetags abgebildet. FX bleibt der originale Wert in 0,1 m/s.

Die [maschinenlesbare Quittung](../../research/observations/knmi_historical_downloads.json)
belegt nur Download und Strukturprüfung. Sie erklärt weder Wiederverwendungsrechte
noch Stationshistorie/Böendauer für geprüft. Die KNMI-Warnung vor Inhomogenitäten
bleibt maßgeblich; diese Rohreihen sind kein Nachweis von Klimatrends.

Reproduktion außerhalb eines Git-Verzeichnisses:

```bash
python research_runners/knmi_historical_wind_acquisition.py --output-dir /external/knmi-historical
python -m unittest tests.test_knmi_historical_wind_acquisition
```

Nächster kausaler Schritt: vollständige 72-Stunden-Ereignisfenster aus den
historischen Originalen erzeugen, Stationshistorien zuordnen und mit den
bereits vorhandenen CLIMK-Originalereignissen vergleichen. Ohne bestätigte
Messvergleichbarkeit bleiben Ergebnisse deskriptiv, keine Bias-Kalibrierung.

Ergebnis des korrigierten Originallaufs: 10/10 Archive geladen und geparst,
17115755 komprimierte Bytes, 876600 Stundenzeilen,
870890 vorhandene und 5710 fehlende FX-Werte.
Keine fehlenden Stunden zwischen den jeweiligen Datei-Endpunkten.
Vollständige Zeitstempel bedeuten somit ausdrücklich nicht vollständige Böenmessungen.

## Historische Ereignisabdeckung tatsächlich ausgeführt

Der [Offline-Prüfer](../../research_runners/knmi_historical_event_coverage.py)
prüft die Original-ZIPs gegen die gespeicherten SHA256-Quittungen und verbindet
sie mit den 50 Ereignisnamen/-daten des ursprünglichen CLIMK-ERA5-NetCDF.
Das untersuchte Fenster umfasst den Vortag ab Stundenende 01 UTC bis zum
Folgetag einschließlich Stundenende 24 UTC. Dies ist eine explizite
Dreitagesfenster-Hypothese; die exakte Quellzeitgrenze ist noch nicht bewiesen.

Ergebnis des Originallaufs: **19 Ereignisse an allen fünf Stationen vollständig**.
Pro Station: 235 → 20, 260 → 21, 280 → 21, 310 → 21, 330 → 19.
Es werden nur Abdeckungsergebnisse ausgegeben, keine kalibrierten Windbias
oder Schäden. Fehlende Stundenzeilen und vorhandene Zeilen ohne FX werden
getrennt gezählt; ein gemessener Nullwert bleibt ein gültiger Wert.

Der vollständige lokale Ergebnisdatensatz liegt außerhalb Git unter
`/dev/shm/knmi-historical-climk-coverage.json`; die Rohdaten sind weiterhin
nicht zur Weiterveröffentlichung zugelassen. Das folgende Kommando erzeugt
sämtliche Ereignis-/Stationsabdeckungen erneut:

```bash
PYTHONPATH=. python research_runners/knmi_historical_event_coverage.py \
  --archive-dir /external/knmi-historical \
  --receipt research/observations/knmi_historical_downloads.json \
  --hazard /external/ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc \
  --output /external/knmi-historical-climk-coverage.json
```

`netCDF4` wird für den Originallauf benötigt; die sieben gemeinsamen
Intake-/Abdeckungstests laufen offline mit der Python-Standardbibliothek.
Sie prüfen auch die 72-Stunden-Grenze, fehlende Werte gegenüber fehlenden
Zeilen und die Ablehnung veränderter Originalbytes.

## Direkter CLI-Aufruf geprüft

Der Ereignisprüfer funktioniert jetzt auch als direkter Skriptaufruf aus
anderen Arbeitsverzeichnissen ohne gesetzten `PYTHONPATH`. Zuvor schlug
sein Import des benachbarten Intake-Moduls fehl. Ein Subprozess-Test entfernt
`PYTHONPATH` explizit und startet `--help` aus `/tmp`. Alle acht lokalen
Intake-/Abdeckungstests bestehen. Für den Originallauf bleibt die optionale
Abhängigkeit `netCDF4` erforderlich; die Hilfe benötigt sie nicht.
