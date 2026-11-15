<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# EIOPA: tatsächlicher Inhalt der vorhandenen Originalworkbooks

Originalprüfung am 14. November 2026 mit
`research_runners/eiopa_wind_workbook_inventory.py`. Die Dateien liegen extern
unter `/tmp/pr-ci/germany-wind-data`; Originalzellen werden nicht veröffentlicht.

- Exposure-Original SHA256:
  `f3ec03e25be247a798d94ea9d5ece8bd03a34bcc27b6faf99b597bbd863c3e79`.
  498 befüllte Datenzeilen, davon 250 Windstorm und 248 Flood, sämtlich
  mit Bezugsjahr 2020. Spalten: Jahr, Risiko, Land, NUTS, NUTS-Name,
  Versicherungssumme in EUR. Keine gebäudegenauen Werte und keine LoB-Spalte.
- Schaden-Original SHA256:
  `201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6`.
  54 Datenzeilen, davon 39 Storm, ausschließlich Ciara Februar 2020;
  weitere Zeilen betreffen Hochwasser und Waldbrand. Keine vollständige
  historische Windschadenzeitreihe.

Die LoB-Kategorien des gesamten Schadenblatts umfassen ALL, COM, RES und
RES+COM. Vor einer Aggregation muss je Land/Ereignis geklärt werden,
welche Kategorien alternative Summen oder disjunkte Bestandteile sind.
Auch die Bedeutung von `Other`, Marktdeckung, Schadenstand, Preisbasis,
NUTS-Version und Deckungen sind vor einem Expositionsnenner-Abgleich offen.
Keine automatische Schadenquote aus diesen beiden Dateien berechnen.

**Nutzbarer nächster Modellfall:** Ciara 2020 mit einem zeitgleichen,
vollständigen Hazard-Footprint und landesweise abgeglichenem versichertem
Bestand. Die vorhandenen CLIMK-Ereignisse 1995–2015 decken Ciara nicht ab;
ein bloßer Index-Join wäre falsch. Das vorhandene ARCO-Stundenexperiment
kann eine Gefährdungsdiagnose unterstützen, ersetzt aber die Ereignis- und
Abdeckungsprüfung nicht. Ciara als Holdout oder Kalibrierfall vorab festlegen.

Der Reader ignoriert formatierungsbedingte Excel-Maximaldimensionen und
zählt tatsächlich befüllte Zeilen. Er inventarisiert Kategorien, liefert
aber weder eine fachliche Zulassung noch eine automatische Schadenaggregation.
Die lokale Ausgabe `/dev/shm/eiopa-wind-inventory.json` enthält das vollständige
Inventar. `openpyxl` ist für den Reader erforderlich.

## Originalabgleich der Ciara-Summen

Der zusätzliche Reader `research_runners/eiopa_lob_reconciliation.py`
prüft ALL gegen die alternativ vorhandenen Komponenten. Beim Originallauf
stimmen alle 15 Länder-/Restgruppen innerhalb eines Eurocents überein.
Die 39 Zeilen sind damit keine 39 unabhängigen Schadenbeträge: ALL darf
nicht zusätzlich zu RES/COM beziehungsweise RES+COM summiert werden.
Das bestätigt die arithmetische Darstellung, nicht Marktdeckung oder
Expositionsnenner. Fehlende Event-IDs werden explizit markiert; ein
fehlender Schlüssel darf nicht automatisch durch einen fremden ersetzt werden.
Die lokale vollständige Auswertung liegt unter
`/dev/shm/eiopa-ciara-lob-reconciliation.json`.

## Länderüberlappung der Originaldateien

Der ausgeführte Abgleich mit `eiopa_country_coverage.compare` findet
für 12 der 15 Ciara-Länder-/Restgruppen ein gleichnamiges Land im
Windstorm-Expositionsblatt. **Schweiz, UK und Other haben dort keinen
passenden Landesnenner.** Other erhält keine erfundene Länderzuordnung.

Die 250 Windstorm-Zeilen verteilen sich auf 30 Länder. Alle geprüften
NUTS-Kennungen sind vier Zeichen lang, ohne doppelte Kennung innerhalb
eines Landes. Das bestätigt keine NUTS-Version oder lückenlose regionale
Abdeckung. Landesüberlappung allein beweist auch keinen gleichen
versicherten Bestand: Sparten, Deckungen und Meldeabdeckung bleiben offen.
Der neue Abgleich gibt deshalb ausdrücklich keine Schadenquote frei.
Die lokale Originalauswertung liegt in `/dev/shm/eiopa-country-overlap.json`.
Sechs lokale Tests der EIOPA-Werkzeuge bestehen.

## Vollständige Reproduktion mit einem Aufruf

```bash
python research_runners/eiopa_ciara_original_review.py \
  --exposure /external/EIOPA-flood-wind-exposure.xlsx \
  --losses /external/EIOPA-historical-loss-data.xlsx \
  --output /external/eiopa-ciara-review.json
```

Dieser Aufruf verbindet Inventar, Spartenabgleich und Länderüberlappung
mit Originalprüfsummen. Er lehnt bereits existierende Ausgaben und einen
geänderten Storm-Ereignisumfang ab. Der Originallauf lieferte 39 Ciara-Zeilen
und 15 Gruppen. Die Ausgabe erklärt den Datensatz weiterhin nicht für
kalibrierungsbereit und erzeugt keine Schadenquoten.
