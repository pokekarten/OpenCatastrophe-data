<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Ereignisinventar über vier originale CLIMK-Quellen

Der [ausführbare Leser](../../research_runners/climk_multisource_event_inventory.py)
wurde mit allen vier lokal vorhandenen Original-NetCDFs ausgeführt: ERA5,
COSMO-REA6, CCLM EUR-11 und CCLM CEU-3. Er erzeugte 200 Quellansichten und
96 Gruppen aus wörtlich gleichem Namen (ohne Groß-/Kleinschreibung) und
gleichem Datumslabel. Jede Ansicht behält Originaldatei, SHA-256, Index,
Sturmname und Datum. Die Ausgabe bleibt außerhalb von Git.

Die 96 Gruppen sind keine 96 nachgewiesenen unabhängigen physischen Stürme.
Datumsfehler, Aliasnamen und zusammengesetzte Stürme erzeugen getrennte
Gruppen; gleiche Labels allein beweisen ebenfalls keine Identität. Es werden
keine unscharfen Namens-/Datumskorrekturen vorgenommen. Quellrankings werden
nicht als Identitäten oder Gewichte verwendet.

Aufruf: `python research_runners/climk_multisource_event_inventory.py`
mit vier wiederholten `--source ORIGINAL.nc` und einem neuen externen
`--output INVENTORY.json`. Der Leser verweigert Überschreiben und doppelte
Quellbytes. Die Dateien bleiben ausgewählte Top-50-Winterereignisse pro
Quelle und erlauben keine vollständigen Jahresraten oder OEP/AEP-Aussagen.

Für einen vollständigen Katalog ist als nächster Zugang das C3S-Produkt
`sis-european-wind-storm-reanalysis` mit originalen Tracks/Ereignisfeldern
zu beschaffen. Der existierende Annual-Summary-Leser liefert lediglich
regionale Jahresindikatoren, keine Sturm-IDs. In der geprüften Umgebung
waren weder CDS-Konfigurationsdatei noch CDSAPI_KEY vorhanden. Ein vollständiger
Katalog benötigt alle unterstützten Jahre einschließlich Nullereignisjahren,
einen festgelegten Tracker, unverwechselbare Ereignis-IDs, Zeitfenster,
Gebiets-/Saisonabdeckung und bei synthetischen Ereignissen dokumentierte
Simulationsjahre und Gewichte. Alternative Tracker und Quellmodelle dürfen
nicht addiert werden.

Dieser Lauf erweitert die ausführbare Mehrsturmgrundlage; der vollständige
jährliche europäische Ereigniskatalog bleibt offen.
