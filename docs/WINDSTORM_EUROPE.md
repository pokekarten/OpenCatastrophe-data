<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Windstorm Europe: Modellstand und Voraussetzungen für den Abschluss

Stand: 14. November 2026. Diese Seite ist der Einstieg für die Fortsetzung
unseres europäischen Windsturm-CAT-Modells. Mit „VinstaMirror“ wird im
Gespräch dieses Windstorm-Europe-Vorhaben verstanden; ein separates Produkt
oder Repository dieses Namens ist nicht nachgewiesen.

## Was bereits im Repository liegt

Der integrierte Forschungsmodellkern verbindet originale CLIMK-Sturmfelder,
GIS-Rasterzellen, Gebäudestandorte, explizite Werte und Antwortklassen,
angenommene Schadenssamples, Policenbedingungen, Ereignisrückversicherung und
vorgegebene Simulationsjahre. Jahresblöcke können gemeinsam gezogen werden;
schadenfreie Jahre bleiben enthalten. Die Datenhäufigkeiten und Schadenmodelle
sind noch nicht als europäisch kalibriert nachgewiesen.

- [Modellkern](../research_runners/windstorm_europe_model_v1.py)
- [Versioniertes fiktives Beispiel](../research/fixtures/windstorm_europe_v1_synthetic.toml)
- [Recherche, Originalquellen, Prüfsummen und tatsächliche Läufe](research/windstorm-europe-v1-rebuild-and-sources.md)
- [Datenbestand und fachliche Lücken](research/windstorm-europe-data-and-completion-gaps-v0.md)
- [Maschinenlesbarer Quellenindex](research/windstorm-europe-source-index-v0.toml)
- [LUISA-2018-Raster- und Kurvenmischungs-Audit](research/windstorm-europe-luisa2018-raster-audit-v0.md)
- [LUISA-Pixel- und Kyrill-Sensitivitätslauf](research/windstorm-europe-luisa-point-sensitivity-v0.md)
- [Physische und finanzielle Modellschritte](research/germany-wind-executable-scenarios-v0.md)

Der Kern wurde über PR #1586 auf `main` integriert, Commit
`8fcb88ec1666702277b30cfe6ab1bc1ddf175412`. Die Jahresblock-Erweiterung aus
PR #1587 ist inzwischen ebenfalls gemergt; GitHub-CI meldete die relevanten
Python-Matrixläufe für 3.11 bis 3.14 erfolgreich. Der letzte gezielte
Offline-Testlauf umfasste 14 erfolgreiche Tests. Ein Testnachweis belegt
Implementierungsverhalten und keine Kalibrierung.

## Was für ein vollständiges Modell konkret benötigt wird

| Baustein | Benötigte Eingaben / Zugriff | Abschlussnachweis |
|---|---|---|
| Modellumfang | Unterstützte Länder, Küsten-/Inselabdeckung, Bezugsjahr, Gebäude-/Inhalts-/BI-Deckungen und Klimaannahme festlegen | Versionierter Umfang; außerhalb liegende Risiken explizit ausgewiesen |
| Ereignisse und Jahresmaß | Vollständige Originalereignisse mit gemeinsamen IDs, Quelltracker, Datum/Zeit, Saison/Jahr, Vollständigkeitsangaben und gegebenenfalls belegten Simulationsgewichten | Nullereignisjahre enthalten; keine Doppelzählung alternativer Tracker, Modelle oder Länder |
| C3S-Zugang | Lokal eingerichtetes CDS-Konto/API-Zugang und erfüllte Bedingungen für das konkrete Produkt | Authentifizierter Originaldownload mit Anfrage, Dateiprüfsumme, Lizenz und Versionsdatum; hier derzeit kein Zugang konfiguriert |
| Gefahrenfelder | Originale Böenfelder je Ereignis, 10-m-Höhe/Böendauer/72h-Fenster, Raster, Masken, full-domain/decontaminated-Variante | Abdeckung jedes modellierten Standorts und Ereignisses geprüft; unbekannte Werte bleiben unbekannt |
| Gebäude | Geometrie/Koordinaten, stabile IDs, Land, Nutzung/Mischnutzung, Größe, Alter, Höhe und Widerstands-/Bauklasse mit Herkunft | Länderabdeckung, Dubletten, Prognoseattribute, Ereignisjahr und Klassenmapping geprüft |
| Werte | Gebäudeersatzwerte, Fläche/Einheiten, Währung und Preisjahr; Inhalte/BI bei entsprechendem Modellumfang separat | Bewertung nachvollziehbar; keine Gleichsetzung von Marktpreis, Grundstückswert und Wiederherstellungswert |
| Schadenantwort | Klassen-/länderspezifische Antwort, Betroffenheit, bedingte Schadenhöhe und Streuung | Gegen kompatible Wind-/Schadenbeobachtungen geprüft; unabhängige Ereignisse als Holdout |
| Abhängigkeit | Räumliche Schadenabhängigkeit innerhalb eines Sturms; Sturmcluster und gegebenenfalls jahresübergreifende Abhängigkeit | Sensitivitäten und empirische Plausibilisierung; angenommene Gruppen bleiben als Annahme erkennbar |
| Versicherung | Policenzuordnung, Deckungen, Selbstbehalte, Limits, Währung, Hours Clauses und Vertragsgrenzen | Einzelpolicen- und Portfoliosummen mit unabhängigem Rechenweg abgeglichen |
| Rückversicherung | Vertragsschichten, Anknüpfung, Limits, Reinstatements und Jahresaggregate | Ereignisreihenfolge und Brutto/Zediert/Netto unter realen Vertragsdefinitionen geprüft |
| Validierung | DWD und weitere nationale Messnetze; passende Markt-/Versichererschäden mit Deckungs-/Gebiets-/Preisjahrdefinition | Kalibrierung und Validierung getrennt; Wind/Hagel und unvollständige Marktabdeckung unterschieden |
| Modellbetrieb | Dauerhaftes Datenarchiv, gepinnte Abhängigkeiten, Original- und abgeleitete Daten getrennt | Reproduktion auf frischer Umgebung, unabhängiger Mehrklassen-Oasis-Abgleich, stabile Jahres-/Tail-Ergebnisse |

Ein reines wirtschaftliches Schadenmodell benötigt keine privaten
Versicherungsverträge. Für belastbare versicherte Brutto-/Nettoverluste sind
sie oder explizit als hypothetisch bezeichnete Vertragsannahmen erforderlich.
Die aktuellen 50 ausgewählten CLIMK-Stürme ersetzen kein Jahresmaß.

## Vorhandene externe Dateien dauerhaft sichern

In dieser Sitzung liegen Originaldateien temporär unter
`/tmp/pr-ci/germany-wind-data` und neue CLIMAAX-Dateien unter
`/dev/shm/windstorm-europe-sources`. Diese Pfade sind kein dauerhaftes Archiv.
Bereits erworben: vier CLIMK-Dateien, XWS-Kyrill, DWD-Archive, NRW-HU2022,
EIOPA-Arbeitsmappen, Schwierz-Referenzen und CLIMAAX-Kurven/Bewertungsdatei.
Erworben bedeutet nicht für jeden fachlichen Zweck geprüft oder freigegeben.

Die CLIMAAX-Arbeitsmappe wurde inzwischen auf Tabellen- und Formelstruktur
geprüft. Sie enthält 46 LUISA-Landnutzungsklassen. Die Spalte `structural
€/m²` ist ein modellierter maximaler Strukturwert je Quadratmeter; die separate
Spalte `content €/m²` folgt aus einem Inhaltsfaktor. Die sechs Bauartanteile
und die Residential/Commercial/Industrial-Mischung sind Landnutzungsannahmen.
Laut offiziellem [CLIMAAX-Handbuch zur maximalen Schadenschätzung](https://handbook.climaax.eu/resources/FAQ/maximum_damages.html)
beruht die Baukostenrelation auf Huizinga et al.; das BIP muss in US-Dollar
des Jahres 2010 eingesetzt werden, das Ergebnis liegt in Euro des Jahres 2010.
Das Handbuch verlangt Währungs- und Inflationsumrechnung auf der Kostenseite.
Damit ist die Tabelle ein nutzbarer, versionierter Landnutzungsproxy, aber
keine aktuelle, gebäudescharfe Versicherungssumme. Für eine Überführung in
Exponierungswerte fehlen mindestens Gebäudegrundfläche bzw. Geschossfläche,
Anzahl/Geschossfläche je Gebäude, passendes Land-/Preisjahr und eine validierte
Zuordnung zwischen Gebäude und LUISA-Zelle. Die integrierte Punktgebäude-Engine
verlangt deshalb weiterhin einen expliziten `building_value_eur`; die LUISA-
Werte werden nicht stillschweigend als solche eingesetzt.

Das im CLIMAAX-Workflow referenzierte [JRC LUISA Base Map 2018](https://data.jrc.ec.europa.eu/dataset/51858b51-8f27-4006-bf82-53eba35a142c)
liegt als 50-m-Raster (Revision VER2026-07-15, EPSG:3035) vor. Der Original-
TIFF-Download (1,019,186,382 Bytes; SHA-256 im Audit) wurde erfolgreich
eingelesen. Punktabfragen aus unseren drei Beispielorten ergaben unter anderem
London=1210, Paris=1111 und Köln=1210. Das sind nur die Landnutzungsklassen der
Pixelmittelpunkte; sie beweisen weder Gebäudezahl noch Gebäudegrundfläche,
Nutzung, Wert oder Widerstand.

Beim Reproduzieren der CLIMAAX-Mischkurven wurde ein konkreter
Spaltenordnungswiderspruch gefunden: Die gepinnte Kurven-CSV nennt ihre zweite
und dritte Spalte `outbuilding strong` und `outbuilding`; das Notebook baut die
Gewichtungsliste als `outbuilding`, `strong outbuilding` und multipliziert
positionsweise. Für LUISA-Klasse 2110 bei 40 m/s ergeben die benannten
Spalten 0,40 %, die positionsweise Notebook-Reihenfolge 2,75 %. Der Unterschied
ist noch nicht mit den Autoren geklärt. Die integrierte Engine mischt diese
Spalten nicht automatisch; bis zur Klärung muss jede Verwendung eine explizite
benannte Zuordnung offenlegen.

Die nächste Umgebung braucht ein persistentes Datenverzeichnis mit genügend
Platz für die tatsächlich ausgewählten regionalen Extrakte. Große europäische
Gebäudebestände partitioniert laden. Originalbytes, Quell-URL, Datum, Lizenz,
Version, Prüfsumme und Transformationsbeschreibung zusammen archivieren.
Die maßgeblichen bekannten Prüfsummen stehen in den verlinkten Berichten
und Quellenbelegen. Lokale Ergebnisse aus `/dev/shm` müssen bei Bedarf anhand
der versionierten Konfiguration neu erzeugt werden.

API-Schlüssel, `.cdsapirc`, private Standorte und Schadeneinzeldaten gehören
in geschützte lokale Konfiguration bzw. zugriffsbeschränkten Datenspeicher,
nicht in Git. Für CDS fehlen in dieser Umgebung sowohl `.cdsapirc` als auch
`CDSAPI_KEY`. Zugang niemals in Issues, PRs oder Chatprotokollen veröffentlichen.

## Reproduzieren und weiterarbeiten

Benötigt: Python 3.11+, NetCDF4-/NumPy-Leser für den Originalgefahrenlauf
sowie die externen Originaldateien. Der Eingabeprüflauf benötigt keine
NetCDF-Auswertung, prüft aber die Originaldatei über ihre Bytes.

```sh
python research_runners/windstorm_europe_model_v1.py \
  --config research/fixtures/windstorm_europe_v1_synthetic.toml \
  --data-dir /data/windstorm-europe --validate-only \
  --output /tmp/windstorm-preflight.json
python research_runners/windstorm_europe_model_v1.py \
  --config research/fixtures/windstorm_europe_v1_synthetic.toml \
  --data-dir /data/windstorm-europe --output /tmp/windstorm-result.json
python -m unittest \
  tests.test_windstorm_europe_year_blocks_v1 \
  tests.test_windstorm_europe_model_v1 \
  tests.test_windstorm_europe_damage_samples_v0 \
  tests.test_windstorm_europe_financial_years_v0 \
  tests.test_germany_wind_scenario_loss_v0 \
  tests.test_climk_building_hazard_join_v0
```

Die Dateien dürfen am Ausgabepfad noch nicht existieren. Das mitgelieferte
Beispiel hat fiktive Gebäude, Werte, Klassen, Vertragsbedingungen und Jahre;
seine AEP/OEP-Werte sind keine beobachteten europäischen Risikokennzahlen.

Nächste kausale Arbeit: persistente Originaldaten verfügbar machen und den
vollständigen Ereigniskatalog beschaffen; parallel bestehende Gebäudeextrakte
klassifizieren und bewerten. Danach Hazard-Abdeckung und Schadenantwort auf
einem größeren länderübergreifenden Portfolio prüfen, die neue Modellkette
unabhängig mit Oasis vergleichen und erst dann Jahresrisiken kalibrieren.
